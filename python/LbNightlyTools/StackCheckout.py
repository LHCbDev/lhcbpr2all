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
from datetime import date

from LbNightlyTools import Configuration
from LbNightlyTools._utils import retry_call as call
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
        u = self.name.upper()
        return os.path.join(u, '{0}_{1}'.format(u, self.version))

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

    def checkout(self, rootdir='.'):
        '''
        Call check out all the projects.
        '''
        __log__.info('checking out stack...')
        for proj in self.projects:
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

        # cache of the project versions
        proj_versions = dict([(p.name, p.version)
                              for p in self.projects])
        proj_versions_uc = dict([(p.name.upper(), p.version)
                                 for p in self.projects])

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

        def fixCMake(proj):
            '''
            Fix the CMake configuration of a project, if it exists, and write
            the changes in 'patchfile'.
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
                    n = line.strip().split()
                    if len(n) == 3 and n[0] == 'use':
                        if n[1] in proj_versions_uc:
                            n[2] = n[1] + '_' + proj_versions_uc[n[1]]
                            # special case
                            if n[2] == 'LCGCMT_preview':
                                n[2] = 'LCGCMT-preview'
                            line = ' '.join(n) + '\n'
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

                newdata = []
                for l in data:
                    n = l.strip().split()
                    if len(n) >= 3 and n[0] == 'use':
                        n[2] = '*'
                        l = ' '.join(n) + '\n'
                    newdata.append(l)

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
        parser = self.parser
        parser.add_option('--build-id',
                          action='store',
                          help='string to add to the tarballs of the build to '
                               'distinguish them from others, the string can '
                               'be a format string using the parameters '
                               '"timestamp" and "slot" (a separation "." will '
                               'be added automatically) [default: %default]')

        parser.add_option('--artifacts-dir',
                          action='store', metavar='DIR',
                          help='directory where to store the artifacts')

        parser.set_defaults(build_id='{slot}.{timestamp}',
                            artifacts_dir='artifacts')

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
        import json
        import codecs

        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        slot = parseConfigFile(self.args[0])

        from datetime import datetime

        starttime = datetime.now()
        timestamp = os.environ.get('TIMESTAMP', date.today().isoformat())

        build_dir = join(os.getcwd(), 'build')

        # replace tokens in the options
        expanded_tokens = {'slot': slot.name, 'timestamp': timestamp}
        for opt_name in ['build_id', 'artifacts_dir']:
            val = getattr(self.options, opt_name)
            if val:
                setattr(self.options, opt_name, val.format(**expanded_tokens))

        artifacts_dir = join(os.getcwd(), self.options.artifacts_dir)

        self.log.info('cleaning directories.')
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        if os.path.exists(artifacts_dir):
            shutil.rmtree(artifacts_dir)

        os.makedirs(build_dir)
        os.makedirs(artifacts_dir)

        # Prepare JSON doc for the database
        os.makedirs(join(artifacts_dir, 'db'))
        cfg = Configuration.load(self.args[0])
        cfg['type'] = 'slot-config'
        cfg['build_id'] = int(os.environ.get('slot_build_id', 0))
        cfg['date'] = timestamp
        f = codecs.open(join(artifacts_dir, 'db',
                             '{slot}.{build_id}'.format(**cfg)), 'w', 'utf-8')
        json.dump(cfg, f)
        f.close()

        slot.checkout(build_dir)

        if not cfg.get('no_patch'):
            slot.patch(build_dir,
                       join(artifacts_dir,
                            '.'.join([self.options.build_id or 'slot',
                                      'patch'])))
        else:
            self.log.info('not patching the sources')

        for proj in slot.projects:
            # ignore missing directories
            # (the project may not have been checked out)
            if not os.path.exists(join(build_dir, proj.projectDir)):
                self.log.warning('no sources for %s, skip packing', proj)
                continue

            self.log.info('packing %s %s...', proj.name, proj.version)

            call(['tar', 'chjf', join(artifacts_dir, self.packname(proj)),
                  proj.projectDir], cwd=build_dir)

        self.log.info('sources ready for build (time taken: %s).',
                      datetime.now() - starttime)
        return 0
