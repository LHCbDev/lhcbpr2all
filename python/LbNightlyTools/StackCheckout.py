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
from LbNightlyTools.Utils import ensureDirs, pack, intPrefix
from LbNightlyTools import CheckoutMethods

__log__ = logging.getLogger(__name__)

class ProjectDesc(object):
    '''
    Describe a project to be checked out.
    '''
    def __init__(self, name, version, **kwargs):
        '''
        @param name: name of the project
        @param version: version of the project as 'vXrY' or 'HEAD', where 'HEAD'
                        means the head version of all the packages
        @param overrides: dictionary describing the differences between the
                          versions of the packages in the requested projects
                          version and the ones required in the checkout
        @param checkout: callable that can check out the specified project
        @param checkout_opts: dictionary with extra options for the
        '''
        self.name = name
        if version.upper() == 'HEAD':
            version = 'HEAD'
        self.version = version
        self.overrides = kwargs.get('overrides', {})
        self._checkout = kwargs.get('checkout', CheckoutMethods.default)
        self.checkout_opts = kwargs.get('checkout_opts', {})

    def checkout(self, rootdir='.'):
        '''
        Helper function to call the checkout method.
        '''
        __log__.info('checking out %s', self)
        self._checkout(self, rootdir=rootdir)

    @property
    def projectDir(self):
        '''Name of the project directory (relative to the build directory).'''
        upcase = self.name.upper()
        return os.path.join(upcase, '{0}_{1}'.format(upcase, self.version))

    def __str__(self):
        '''String representation of the project.'''
        return "{0} {1}".format(self.name, self.version)

class StackDesc(object):
    '''
    Class describing a software stack.
    '''
    def __init__(self, projects=None, name=None):
        self.name = name
        self.projects = projects or []

    def checkout(self, rootdir='.', requested=None):
        '''
        Call check out all the (requested) projects.
        '''
        __log__.info('checking out stack...')
        for proj in self.projects:
            # Consider only requested projects (if there was a selection)
            if requested and proj.name.lower() not in requested:
                continue # project not requested: skip
            proj.checkout(rootdir)
        __log__.info('... done.')

    def patch(self, rootdir='.', patchfile='stack.patch'):
        '''
        Take all projects/packages in the stack and fix the dependencies to make
        a consistent set.
        '''
        import re
        from os.path import exists, join
        from difflib import context_diff

        gp_exp = re.compile(r'gaudi_project\(([^)]+)\)')
        ht_exp = re.compile(r'set\(\s*heptools_version\s+([^)]+)\)')

        # cache of the project versions
        proj_versions = dict([(p.name, p.version)
                              for p in self.projects])
        proj_versions_uc = dict([(p.name.upper(), p.version)
                                 for p in self.projects])
        # FIXME: we will need to handle the _preview/-preview case
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
            cmakelists = join(proj.projectDir, 'CMakeLists.txt')

            if exists(join(rootdir, cmakelists)):
                __log__.info('patching %s', cmakelists)
                f = open(join(rootdir, cmakelists))
                data = f.read()
                f.close()
                try:
                    # find the project declaration call
                    m = gp_exp.search(data)
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
            toolchain = join(proj.projectDir, 'toolchain.cmake')

            if exists(join(rootdir, toolchain)):
                __log__.info('patching %s', toolchain)
                f = open(join(rootdir, toolchain))
                data = f.read()
                f.close()
                try:
                    # find the heptools version setting
                    m = ht_exp.search(data)
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
            project_cmt = join(proj.projectDir, 'cmt', 'project.cmt')

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
                            if tokens[1] != 'LCGCMT':
                                tokens[2] = (tokens[1] + '_'
                                             + proj_versions_uc[tokens[1]])
                            else: # LCGCMT is special
                                # if the version is 'preview' or the numeric
                                # prefix is >= 68 the version string is
                                #   LCGCMT-<version>
                                # otherwise
                                #   LCGCMT_<version>
                                lcg_ver = proj_versions_uc[tokens[1]]
                                lcg_num_ver = intPrefix(lcg_ver)
                                if (lcg_ver == 'preview' or lcg_num_ver >= 68):
                                    tokens[2] = 'LCGCMT-' + lcg_ver
                                else:
                                    tokens[2] = 'LCGCMT_' + lcg_ver
                            line = ' '.join(tokens) + '\n'
                    newdata.append(line)

                f = open(join(rootdir, project_cmt), 'w')
                f.writelines(newdata)
                f.close()

                write_patch(data, newdata, project_cmt)

            # find the container package
            requirements = join(proj.projectDir, proj.name + 'Release',
                                'cmt', 'requirements')
            if not exists(join(rootdir, requirements)):
                requirements = join(proj.projectDir, proj.name + 'Sys',
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

def parseConfigFile(path):
    '''
    Load the slot configuration file and translate it in a StackDesc instance.
    '''
    data = Configuration.load(path)
    projects = []
    old_checkout_names = {'defaultCheckout': 'default',
                          'gitCheckout': 'git',
                          'noCheckout': 'ignore'}
    for proj in data[u'projects']:
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
        projects.append(ProjectDesc(proj[u'name'], proj[u'version'],
                                    overrides=proj.get(u'overrides', {}),
                                    checkout=checkout,
                                    checkout_opts=proj.get(u'checkout_opts',
                                                           {})))
    return StackDesc(projects=projects, name=data.get(u'slot', None))

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

    def packname(self, proj):
        '''
        Return the filename of the archive (package) of the given project.
        '''
        packname = [proj.name, proj.version]
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

        from datetime import datetime

        starttime = datetime.now()
        timestamp = os.environ.get('TIMESTAMP', date.today().isoformat())

        build_dir = join(os.getcwd(), 'tmp', 'checkout')

        expandTokensInOptions(opts, ['build_id', 'artifacts_dir'],
                              slot=slot.name, timestamp=timestamp)

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
        cfg['date'] = timestamp
        Dashboard(credentials=None,
                  dumpdir=join(artifacts_dir, 'db'),
                  submit=opts.submit,
                  flavour=opts.flavour).publish(cfg)
        # Save a copy as metadata for tools like lbn-install
        with codecs.open(join(artifacts_dir, 'slot-config.json'),
                         'w', 'utf-8') as config_dump:
            json.dump(cfg, config_dump, indent=2)

        slot.checkout(build_dir, opts.projects)

        if not cfg.get('no_patch'):
            slot.patch(build_dir,
                       join(artifacts_dir,
                            '.'.join([opts.build_id or 'slot', 'patch'])))
        else:
            self.log.info('not patching the sources')

        for proj in slot.projects:
            # ignore missing directories
            # (the project may not have been checked out)
            if not os.path.exists(join(build_dir, proj.projectDir)):
                self.log.warning('no sources for %s, skip packing', proj)
                continue

            self.log.info('packing %s %s...', proj.name, proj.version)

            pack([proj.projectDir], join(artifacts_dir, self.packname(proj)),
                 cwd=build_dir, checksum='md5')

        self.log.info('sources ready for build (time taken: %s).',
                      datetime.now() - starttime)
        return 0
