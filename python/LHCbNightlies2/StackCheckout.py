#!/usr/bin/env python
'''
Module containing the classes and functions used to checkout a set of projects,
fixing their dependencies to produce a consistent set.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import logging
import shutil
import os
import sys
import subprocess
from datetime import date

log = logging.getLogger(__name__)

def call(*args, **kwargs):
    '''
    Replacement for subprocess.call() that can retry if the command fails.
    To enable the retries, pass the keyword argument 'retry' setting it to the
    number of timed to try.

    For example:

    >>> call(['false'], retry=3)
    Traceback (most recent call last):
    ...
    RuntimeError: the command ['false'] failed 3 times

    '''
    if 'retry' not in kwargs:
        # no retry
        return subprocess.call(*args, **kwargs)
    else:
        retry = kwargs.pop('retry')
        for _count in range(retry):
            if subprocess.call(*args, **kwargs) == 0:
                break
        else: # Note: else of the 'for' block
            raise RuntimeError('the command {0} failed {1} times'
                                .format(args[0], retry))
        return 0

def defaultCheckout(desc, rootdir='.'):
    '''
    Checkout the project described by the ProjectDesc 'desc'.
    '''
    getpack = ['getpack', '--batch', '--no-config']
    log.debug('checking out %s', desc)
    cmd = getpack + ['-P',
                     '-H' if desc.version == 'HEAD' else '-r',
                     desc.name, desc.version]
    call(cmd, cwd=rootdir, retry=3)

    prjroot = os.path.normpath(os.path.join(rootdir, desc.projectDir))

    overrides = desc.overrides
    if overrides:
        log.debug('overriding packages')
        for package, version in overrides.items():
            if version:
                cmd = getpack + [package, version]
                call(cmd, cwd=prjroot, retry=3)
            else:
                print 'Removing', package
                shutil.rmtree(os.path.join(prjroot, package), ignore_errors=True)

    log.debug('checkout of %s completed in %s', desc, prjroot)

def noCheckout(desc, rootdir='.'):
    '''
    Special checkout function used to just declare a project version in the
    configuration but do not perform the checkout, so that it's picked up from
    the release area.
    '''
    log.info('checkout not requested for %s', desc)

class ProjectDesc(object):
    '''
    Describe a project to be checked out.
    '''
    def __init__(self, name, version, overrides=None, checkout=None):
        '''
        @param name: name of the project
        @param version: version of the project as 'vXrY' or 'HEAD', where 'HEAD'
                        means the head version of all the packages
        @param overrides: dictionary describing the differences between the
                          versions of the packages in the requested projects
                          version and the ones required in the checkout
        @param checkout: callable that can check out the specified project
        '''
        self.name = name
        if version.upper() == 'HEAD':
            version = 'HEAD'
        self.version = version
        self.overrides = overrides or {}
        self._checkout = checkout or defaultCheckout

    def checkout(self, rootdir='.'):
        '''
        Helper function to call the checkout method.
        '''
        log.info('checking out %s', self)
        self._checkout(self, rootdir=rootdir)

    @property
    def projectDir(self):
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
        log.info('checking out stack...')
        for p in self.projects:
            p.checkout(rootdir)
        log.info('... done.')

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
        projVersions = dict([(p.name, p.version) for p in self.projects])
        PROJVersions = dict([(p.name.upper(), p.version) for p in self.projects])

        patchfile = open(join(rootdir, patchfile), 'w')

        def fixCMake(p):
            '''
            Fix the CMake configuration of a project, if it exists, and write
            the changes in 'patchfile'.
            '''
            cmakelists = join(p.projectDir, 'CMakeLists.txt')

            if exists(join(rootdir, cmakelists)):
                log.info('patching %s', cmakelists)
                f = open(join(rootdir, cmakelists))
                data = f.read()
                f.close()

                # find the project declaration call
                m = gp_exp.search(data)
                args = m.group(1).split()
                args[1] = p.version # the project version is always the second

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
                        args[i+1] = projVersions.get(args[i], args[i+1])
                # FIXME: we should take into account the declared dependencies
                newdata = data[:m.start(1)] + ' '.join(args) + data[m.end(1):]

                f = open(join(rootdir, cmakelists), 'w')
                f.write(newdata)
                f.close()

                patchfile.writelines(context_diff(data.splitlines(True),
                                                  newdata.splitlines(True),
                                                  fromfile=join('a', cmakelists),
                                                  tofile=join('b', cmakelists)))

        def fixCMT(p):
            '''
            Fix the CMT configuration of a project, if it exists, and write
            the changes in 'patchfile'.
            '''
            project_cmt = join(p.projectDir, 'cmt', 'project.cmt')

            if exists(join(rootdir, project_cmt)):
                log.info('patching %s', project_cmt)
                f = open(join(rootdir, project_cmt))
                data = f.readlines()
                f.close()

                newdata = []
                for l in data:
                    n = l.strip().split()
                    if len(n) == 3 and n[0] == 'use':
                        if n[1] in PROJVersions:
                            n[2] = n[1] + '_' + PROJVersions[n[1]]
                            # special case
                            if n[2] == 'LCGCMT_preview':
                                n[2] = 'LCGCMT-preview'
                            l = ' '.join(n) + '\n'
                    newdata.append(l)

                f = open(join(rootdir, project_cmt), 'w')
                f.writelines(newdata)
                f.close()

                patchfile.writelines(context_diff(data, newdata,
                                                  fromfile=join('a', project_cmt),
                                                  tofile=join('b', project_cmt)))

            # find the container package
            requirements = join(p.projectDir, p.name + 'Release', 'cmt', 'requirements')
            if not exists(join(rootdir, requirements)):
                requirements = join(p.projectDir, p.name + 'Sys', 'cmt', 'requirements')

            if exists(join(rootdir, requirements)):
                log.info('patching %s', requirements)
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

                patchfile.writelines(context_diff(data, newdata,
                                                  fromfile=join('a', requirements),
                                                  tofile=join('b', requirements)))

        for p in self.projects:
            fixCMake(p)
            fixCMT(p)

        patchfile.close()


def specialGaudiCheckout(desc, rootdir='.'):
    dest = os.path.join(rootdir, desc.projectDir)
    call(['git', 'clone', '-b', 'dev/cmake',
          'http://cern.ch/gaudi/Gaudi.git', dest])
    f = open(os.path.join(dest, 'Makefile'), 'w')
    f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
    f.close()

def specialLHCbCheckout(desc, rootdir='.'):
    getpack = ['getpack', '--batch', '--no-config']
    log.debug('checking out %s', desc)
    cmd = getpack + ['-P', desc.name, desc.version]
    call(cmd, cwd=rootdir, retry=3)

def parseConfigFile(path):
    import json
    data = json.load(open(path))
    projects = []
    for p in data[u'projects']:
        checkout = p.get(u'checkout', 'defaultCheckout')
        if '.' in checkout:
            m, f = checkout.rsplit('.', 1)
            checkout = getattr(__import__(m, fromlist=[f]), f)
        else:
            checkout = globals()[checkout]
        projects.append(ProjectDesc(p[u'name'], p[u'version'],
                                    overrides=p.get(u'overrides', {}),
                                    checkout=checkout))
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
                               'distinguish them from others, the string can be a '
                               'format string using the parameters "timestamp" '
                               'and "slot" (a separation "." will '
                               'be added automatically) [default: %default]')

        parser.set_defaults(build_id='{slot}.{timestamp}')

    def main(self):
        """ User code place holder """
        from os.path import join

        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        slot = parseConfigFile(self.args[0])

        build_dir = join(os.getcwd(), 'build')
        sources_dir = join(os.getcwd(), 'sources')

        from datetime import datetime
        starttime = datetime.now()

        timestamp = date.today().isoformat()

        self.log.info('cleaning directories.')
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        if os.path.exists(sources_dir):
            shutil.rmtree(sources_dir)

        os.makedirs(build_dir)
        os.makedirs(sources_dir)

        slot.checkout(build_dir)

        slot.patch(build_dir,
                   join(sources_dir, '.'.join([slot.name, timestamp, 'patch'])))

        for p in slot.projects:
            # ignore missing directories (the project may not have been checked out)
            if not os.path.exists(join(build_dir, p.projectDir)):
                self.log.warning('no sources for %s, skip packing', p)
                continue

            self.log.info('packing %s %s...', p.name, p.version)
            packname = [p.name, p.version]
            if self.opts.build_id:
                packname.append(self.opts.build_id.format(slot=slot.name,
                                                          timestamp=timestamp))
            packname.append('src')
            packname.append('tar.bz2')
            packname = '.'.join(packname)

            call(['tar', 'chjf', join(sources_dir, packname),
                  p.projectDir], cwd=build_dir)

        self.log.info('sources ready for build (time taken: %s).', datetime.now() - starttime)
        return 0


if __name__ == '__main__':
    sys.exit(Script().run())
