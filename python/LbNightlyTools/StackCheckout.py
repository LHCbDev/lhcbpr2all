###############################################################################
# (c) Copyright 2013 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
'''
Module containing the classes and functions used to checkout a set of projects,
fixing their dependencies to produce a consistent set.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import logging
import shutil
import os
import json
import codecs
from datetime import date

from LbNightlyTools import Configuration
from LbNightlyTools.Configuration import GP_EXP, HT_EXP, Project
from LbNightlyTools.Utils import ensureDirs, pack, setenv, shallow_copytree
from LbNightlyTools.Utils import find_path, IgnorePackageVersions
from LbNightlyTools import CheckoutMethods

__log__ = logging.getLogger(__name__)


class PackageDesc(object):
    '''
    Describe a package to be checked out.
    '''
    def __init__(self, name, version, **kwargs):
        '''
        @param name: name of the package
        @param version: version of the package as 'vXrY' or 'HEAD'
        @param container: name of the container project ('DBASE' or 'PARAM')
        @param checkout: callable that can check out the specified project
        @param checkout_opts: dictionary with extra options for the checkout
                              callable
        '''
        self.name = name
        if version.lower() == 'head':
            version = 'head'
        self.version = version
        self.container = kwargs.get('container', 'DBASE')
        self._checkout = kwargs.get('checkout', CheckoutMethods.default)
        self.checkout_opts = kwargs.get('checkout_opts', {})
        self.isProject = False
        self.isPackage = True

    def checkout(self, rootdir='.'):
        '''
        Helper function to call the checkout method.
        '''
        __log__.info('checking out %s', self)
        self._checkout(self, rootdir=rootdir)

    @property
    def baseDir(self):
        '''Name of the package directory (relative to the build directory).'''
        return os.path.join(self.container, self.name, self.version)

    def build(self, rootdir='.'):
        '''
        Build the package and return the return code of the build process.
        '''
        from subprocess import Popen
        base = os.path.join(rootdir, self.baseDir)
        if os.path.exists(os.path.join(base, 'Makefile')):
            __log__.info('building %s (make)', self)
            return Popen(['make'], cwd=base).wait()
        elif os.path.exists(os.path.join(base, 'cmt', 'requirements')):
            __log__.info('building %s (cmt make)', self)
            # CMT is very sensitive to these variables (better to unset them)
            env = dict((key, value) for key, value in os.environ.items()
                        if key not in ('PWD', 'CWD', 'CMTSTRUCTURINGSTYLE'))
            base = os.path.join(base, 'cmt')
            Popen(['cmt', 'config'], cwd=base, env=env).wait()
            return Popen(['cmt', 'make'], cwd=base, env=env).wait()
        __log__.info('%s does not require build', self)
        return 0

    def getVersionLinks(self, rootdir='.'):
        '''
        Return a list of version aliases for the current package (only if the
        requested version is head).
        '''
        if self.version != 'head':
            return []
        base = os.path.join(rootdir, self.baseDir)
        aliases = ['v999r999']
        print os.path.exists(os.path.join(base, 'cmt', 'requirements'))
        if os.path.exists(os.path.join(base, 'cmt', 'requirements')):
            for l in open(os.path.join(base, 'cmt', 'requirements')):
                l = l.strip()
                if l.startswith('version'):
                    version = l.split()[1]
                    aliases.append(version[:version.rfind('r')] + 'r999')
                    break
        return aliases

    def __str__(self):
        '''String representation of the project.'''
        return "{0} {1}".format(self.name, self.version)


class StackDesc(object):
    '''
    Class describing a software stack.
    '''
    def __init__(self, projects=None, packages=None, name=None, env=None):
        self.name = name
        self.projects = projects or []
        self.packages = packages or []
        self.env = env or []

    def checkout(self, rootdir='.', requested=None, ignore_failures=True):
        '''
        Call check out all the (requested) projects.
        '''
        __log__.info('checking out stack...')
        if self.packages:
            for pkg in self.packages:
                try:
                    pkg.checkout(rootdir)
                except RuntimeError, err:
                    if not ignore_failures:
                        raise
                    __log__.warning(str(err))

            __log__.debug('create shallow clones of DBASE and PARAM')
            # clone the container projects
            ignore = IgnorePackageVersions(self.packages)
            for container in ('DBASE', 'PARAM'):
                if not os.path.exists(os.path.join(rootdir, container)):
                    continue
                path = find_path(container)
                if path:
                    shallow_copytree(path, os.path.join(rootdir, container),
                                     ignore)

            for pkg in self.packages:
                if os.path.exists(os.path.join(rootdir, pkg.baseDir)):
                    if pkg.build(rootdir) != 0:
                        __log__.warning('%s build failed', pkg)
                    for link in pkg.getVersionLinks(rootdir):
                        __log__.debug('creating symlink %s', link)
                        os.symlink(pkg.version,
                                   os.path.normpath(os.path.join(rootdir,
                                                                 pkg.baseDir,
                                                                 os.pardir,
                                                                 link)))
                else:
                    __log__.warning('package %s not found', pkg)


        for proj in self.projects:
            # Consider only requested projects (if there was a selection)
            if requested and proj.name.lower() not in requested:
                continue # project not requested: skip
            try:
                proj.checkout(rootdir)
            except RuntimeError, err:
                if not ignore_failures:
                    raise
                __log__.warning(str(err))
        __log__.info('... done.')

    def patch(self, rootdir='.', patchfile='stack.patch'):
        '''
        Take all projects/packages in the stack and fix the dependencies to make
        a consistent set.
        '''
        from os.path import exists, join
        from difflib import context_diff

        # cache of the project versions
        proj_versions = dict([(p.name, p.version)
                              for p in self.projects])
        proj_versions_uc = dict([(p.name.upper(), p.version)
                                 for p in self.projects])
        heptools_version = proj_versions_uc.get('HEPTOOLS',
                                                proj_versions_uc.get('LCGCMT'))

        pfile = open(join(rootdir, patchfile), 'w')
        def write_patch(data, newdata, filename):
            '''
            Write the difference between data and newdata in the patchfile.
            '''
            if hasattr(data, 'splitlines'):
                data = data.splitlines(True)
            if hasattr(newdata, 'splitlines'):
                newdata = newdata.splitlines(True)
            pfile.writelines(context_diff(data, newdata,
                                          fromfile=join('a', filename),
                                          tofile=join('b', filename)))

        def fixCMakeLists(proj):
            '''
            Fix the 'CMakeLists.txt'.
            '''
            cmakelists = join(proj.baseDir, 'CMakeLists.txt')

            if exists(join(rootdir, cmakelists)):
                __log__.info('patching %s', cmakelists)
                f = open(join(rootdir, cmakelists))
                data = f.read()
                f.close()
                try:
                    # find the project declaration call
                    m = GP_EXP.search(data)
                    if m is None:
                        __log__.warning('%s does not look like a Gaudi/CMake '
                                        'project, I\'m not touching it', proj)
                        return
                    args = m.group(1).split()
                    # the project version is always the second
                    args[1] = proj.version

                    # fix the dependencies
                    if 'USE' in args:
                        # look for the indexes of the range 'USE' ... 'DATA'
                        use_idx = args.index('USE') + 1
                        if 'DATA' in args:
                            data_idx = args.index('DATA')
                        else:
                            data_idx = len(args)
                        # for each key, get the version (if available)
                        for i in range(use_idx, data_idx, 2):
                            args[i+1] = proj_versions.get(args[i], args[i+1])
                    # FIXME: we should take into account the declared deps
                    start, end = m.start(1), m.end(1)
                    newdata = data[:start] + ' '.join(args) + data[end:]
                except: # pylint: disable=W0702
                    __log__.error('failed parsing of %s, not patching it',
                                  cmakelists)
                    return

                f = open(join(rootdir, cmakelists), 'w')
                f.write(newdata)
                f.close()

                write_patch(data, newdata, cmakelists)

        def fixCMakeToolchain(proj):
            '''
            Fix 'toolchain.cmake'.
            '''
            toolchain = join(proj.baseDir, 'toolchain.cmake')

            if exists(join(rootdir, toolchain)):
                __log__.info('patching %s', toolchain)
                f = open(join(rootdir, toolchain))
                data = f.read()
                f.close()
                try:
                    # find the heptools version setting
                    m = HT_EXP.search(data)
                    if m is None:
                        __log__.debug('%s does not set heptools_version, '
                                      'no need to touch', proj)
                        return
                    start, end = m.start(1), m.end(1)
                    newdata = data[:start] + heptools_version + data[end:]
                except: # pylint: disable=W0702
                    __log__.error('failed parsing of %s, not patching it',
                                  toolchain)
                    return

                f = open(join(rootdir, toolchain), 'w')
                f.write(newdata)
                f.close()

                write_patch(data, newdata, toolchain)

        def fixCMake(proj):
            '''
            Fix the CMake configuration of a project, if it exists, and write
            the changes in 'patchfile'.
            '''
            fixCMakeLists(proj)
            if heptools_version:
                fixCMakeToolchain(proj)

        def fixCMT(proj):
            '''
            Fix the CMT configuration of a project, if it exists, and write
            the changes in 'patchfile'.
            '''
            project_cmt = join(proj.baseDir, 'cmt', 'project.cmt')

            if exists(join(rootdir, project_cmt)):
                __log__.info('patching %s', project_cmt)
                f = open(join(rootdir, project_cmt))
                data = f.readlines()
                f.close()

                newdata = []
                for line in data:
                    tokens = line.strip().split()
                    if len(tokens) == 3 and tokens[0] == 'use':
                        if tokens[1] in proj_versions_uc:
                            tokens[2] = (tokens[1] + '_'
                                         + proj_versions_uc[tokens[1]])
                            line = ' '.join(tokens) + '\n'
                    newdata.append(line)

                f = open(join(rootdir, project_cmt), 'w')
                f.writelines(newdata)
                f.close()

                write_patch(data, newdata, project_cmt)

            # find the container package
            requirements = join(proj.baseDir, proj.name + 'Release',
                                'cmt', 'requirements')
            if not exists(join(rootdir, requirements)):
                requirements = join(proj.baseDir, proj.name + 'Sys',
                                    'cmt', 'requirements')

            if exists(join(rootdir, requirements)):
                __log__.info('patching %s', requirements)
                f = open(join(rootdir, requirements))
                data = f.readlines()
                f.close()

                used_pkgs = set()

                newdata = []
                for line in data:
                    tokens = line.strip().split()
                    if len(tokens) >= 3 and tokens[0] == 'use':
                        tokens[2] = '*'
                        if len(tokens) >= 4 and tokens[3][0] not in ('-', '#'):
                            used_pkgs.add('{3}/{1}'.format(*tokens))
                        else:
                            used_pkgs.add(tokens[1])
                        line = ' '.join(tokens) + '\n'
                    newdata.append(line)

                for added_pkg in set(proj.overrides.keys()) - used_pkgs:
                    if '/' in added_pkg:
                        hat, added_pkg = added_pkg.rsplit('/', 1)
                    else:
                        hat = ''
                    newdata.append('use {0} * {1}\n'.format(added_pkg, hat))

                f = open(join(rootdir, requirements), 'w')
                f.writelines(newdata)
                f.close()

                write_patch(data, newdata, requirements)

        for proj in self.projects:
            fixCMake(proj)
            fixCMT(proj)

        pfile.close()

    def collectDeps(self, rootdir='.'):
        '''
        Scan the configuration files of the projects to discover their
        dependencies.
        @return: dictionary with project names as keys and list of dep as values
        '''
        # helper dict to map case insensitive name to correct project names
        names = dict((p.name.lower(), p.name) for p in self.projects)
        deps = {}
        for p in self.projects:
            # note that we ignore projects not in the stack
            deps[p.name] = [names[n]
                            for n in p.getDeps(rootdir)
                            if n in names]
        return deps

    def package(self, name):
        '''
        Return the package with the given name.
        '''
        name = name.lower()
        for p in self.packages:
            if p.name.lower() == name:
                return p
        return None

    def project(self, name):
        '''
        Return the project with the given name.
        '''
        name = name.lower()
        for p in self.projects:
            if p.name.lower() == name:
                return p
        return None


def parseConfigFile(path):
    '''
    Load the slot configuration file and translate it in a StackDesc instance.
    '''
    data = Configuration.load(path)
    packages = []
    for pkg in data.get(u'packages', []):
        checkout = pkg.get(u'checkout', 'default')
        if '.' in checkout:
            m, f = checkout.rsplit('.', 1)
            checkout = getattr(__import__(m, fromlist=[f]), f)
        else:
            checkout = getattr(CheckoutMethods, checkout)
        packages.append(PackageDesc(pkg[u'name'], pkg[u'version'],
                                    container=pkg.get(u'container', 'DBASE'),
                                    checkout=checkout,
                                    checkout_opts=pkg.get(u'checkout_opts',
                                                           {})))
    projects = []
    old_checkout_names = {'defaultCheckout': 'default',
                          'gitCheckout': 'git',
                          'noCheckout': 'ignore'}
    for proj in data.get(u'projects', []):
        checkout = proj.get(u'checkout', 'default')
        # add backward compatibility check for the checkout functions
        if checkout in old_checkout_names:
            new_name = old_checkout_names[checkout]
            __log__.warning('the checkout name "%s" is deprecated, '
                            'use "%s" instead', checkout, new_name)
            checkout = new_name
        if '.' in checkout:
            m, f = checkout.rsplit('.', 1)
            checkout = getattr(__import__(m, fromlist=[f]), f)
        else:
            checkout = getattr(CheckoutMethods, checkout)
        projects.append(Project(proj[u'name'], proj[u'version'],
                                overrides=proj.get(u'overrides', {}),
                                checkout=checkout,
                                checkout_opts=proj.get(u'checkout_opts',
                                                           {})))
    return StackDesc(projects=projects, packages=packages,
                     name=data.get(u'slot', None),
                     env=data.get(u'env', []))

import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Script to checkout a consistent set of projects as described in a
    configuration file.

    The configuration file must be in JSON format containing an object with the
    attribute 'projects', a list of objects with defining the projects to be
    checked out.

    For example::
        {"projects": [{"name": "Gaudi",
                       "version": "v23r5",
                       "checkout": "specialCheckoutFunction"},
                      {"name": "LHCb",
                       "version": "v32r5",
                       "overrides": {"GaudiObjDesc": "HEAD",
                                     "GaudiPython": "v12r4",
                                     "Online/RootCnv": null}}]}
    '''
    __usage__ = '%prog [options] <config.json>'
    __version__ = ''

    def defineOpts(self):
        """ User options -- has to be overridden """
        from LbNightlyTools.ScriptsCommon import (addBasicOptions,
                                                  addDashboardOptions)
        addBasicOptions(self.parser)
        addDashboardOptions(self.parser)

        self.parser.add_option('--ignore-checkout-errors',
                               action='store_true',
                               dest='ignore_checkout_errors',
                               help='continue to checkout if there is a '
                                    'failure (default)')
        self.parser.add_option('--no-ignore-checkout-errors',
                               action='store_false',
                               dest='ignore_checkout_errors',
                               help='stop the checkout if there is a failure')
        self.parser.set_defaults(ignore_checkout_errors=True)

    def packname(self, element):
        '''
        Return the filename of the archive (package) of the given project.
        '''
        packname = [element.name.replace('/', '_'), element.version]
        if self.options.build_id:
            packname.append(self.options.build_id)
        packname.append('src')
        packname.append('tar.bz2')
        return '.'.join(packname)

    def main(self):
        """ User code place holder """
        from os.path import join
        from LbNightlyTools.Utils import Dashboard
        from LbNightlyTools.ScriptsCommon import expandTokensInOptions

        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        opts = self.options

        slot = parseConfigFile(self.args[0])

        # prepare special environment, if needed
        setenv(slot.env)

        from datetime import datetime

        starttime = datetime.now()

        build_dir = join(os.getcwd(), 'tmp', 'checkout')

        expandTokensInOptions(opts, ['build_id', 'artifacts_dir'],
                              slot=slot.name)

        artifacts_dir = join(os.getcwd(), opts.artifacts_dir)

        if opts.projects:
            opts.projects = set(p.strip().lower()
                                for p in opts.projects.split(','))
        else:
            opts.projects = None

        self.log.debug('cleaning checkout directory')
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

        ensureDirs([build_dir, artifacts_dir, join(artifacts_dir, 'db')])

        # Prepare JSON doc for the database
        ensureDirs([join(artifacts_dir, 'db')])
        cfg = Configuration.load(self.args[0])
        cfg['type'] = 'slot-config'
        cfg['build_id'] = int(os.environ.get('slot_build_id', 0))
        cfg['date'] = os.environ.get('DATE', date.today().isoformat())
        cfg['started'] = starttime.isoformat()
        platforms = os.environ.get('platforms', '').strip().split()
        if platforms:
            cfg['platforms'] = platforms
        dashboard = Dashboard(credentials=None,
                              dumpdir=join(artifacts_dir, 'db'),
                              submit=opts.submit,
                              flavour=opts.flavour)
        # publish the configuration before the checkout
        # (but we have to update it later)
        dashboard.publish(cfg)

        slot.checkout(build_dir, opts.projects,
                      ignore_failures=opts.ignore_checkout_errors)

        if not cfg.get('no_patch'):
            slot.patch(build_dir,
                       join(artifacts_dir,
                            '.'.join([opts.build_id or 'slot', 'patch'])))
        else:
            self.log.info('not patching the sources')

        deps = slot.collectDeps(build_dir)
        for p in cfg.get('projects', []):
            p['dependencies'] = sorted(set(p.get('dependencies', []) +
                                           deps.get(p['name'], [])))
        # add dependencies of data packages on the corresponding container
        containers = set()
        for p in cfg.get('packages', []):
            container = slot.package(p['name']).container
            containers.add(container)
            p['dependencies'] = sorted(set(p.get('dependencies', []) +
                                           [container]))

        # ensure that we have a project list in the configuration if we need
        # to add the containers
        if containers and 'projects' not in cfg:
            cfg['projects'] = []
        # I believe it's nicer if the container projects are at the top
        # of the list in alphabetical order
        for p in sorted(containers, reverse=True):
            # Note that we add the containers only to the configuration and not
            # to the slot object.
            if slot.project(p) is None:
                cfg['projects'].insert(0,{'name': p,
                                          'version': 'None',
                                          'checkout': 'ignore'})

        for element in slot.projects + slot.packages:
            # ignore missing directories
            # (the project may not have been checked out)
            if not os.path.exists(join(build_dir, element.baseDir)):
                self.log.warning('no sources for %s, skip packing', element)
                continue

            self.log.info('packing %s %s...', element.name, element.version)

            pack([element.baseDir], join(artifacts_dir, self.packname(element)),
                 cwd=build_dir, checksum='md5')
        for container in containers:
            self.log.info('packing %s (links)...', container)
            contname = [container]
            if self.options.build_id:
                contname.append(self.options.build_id)
            contname.append('src.tar.bz2')
            pack([container], join(artifacts_dir, '.'.join(contname)),
                 cwd=build_dir, checksum='md5', dereference=False,
                 exclude=[p.baseDir for p in slot.packages])

        # Save a copy as metadata for tools like lbn-install
        with codecs.open(join(artifacts_dir, 'slot-config.json'),
                         'w', 'utf-8') as config_dump:
            json.dump(cfg, config_dump, indent=2)

        # publish the updated configuration JSON
        dashboard.publish(cfg)

        self.log.info('sources ready for build (time taken: %s).',
                      datetime.now() - starttime)
        return 0
