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

log = logging.getLogger(__name__)

def call(*args, **kwargs):
    '''
    Replacement for subprocess.call() that can retry if the command fails.
    To enable the retries, pass the keyword argument
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

class ProjectDesc(object):
    '''
    Describe a project to be checked out.
    '''
    def __init__(self, name, version, overrides=None, checkout=defaultCheckout):
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
        self.overrides = overrides if overrides else {}
        self._checkout = checkout

    def checkout(self, rootdir='.'):
        '''
        Helper function to call the checkout method.
        '''
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
    def __init__(self, projects=None):
        self.projects = projects if projects else []

    def checkout(self, rootdir='.'):
        '''
        Call check out all the projects.
        '''
        for p in self.projects:
            p.checkout(rootdir)

def specialGaudiCheckout(desc, rootdir='.'):
    dest = os.path.join(rootdir, desc.projectDir)
    call(['git', 'clone', '-b', 'dev/cmake',
          'http://cern.ch/gaudi/Gaudi.git', dest])
    f = open(os.path.join(dest, 'Makefile'), 'w')
    f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
    f.close()

def parseConfigFile(path):
    import json
    data = json.load(open(path))
    projects = []
    for p in data[u'projects']:
        if u'checkout' in p:
            checkout = globals()[p[u'checkout']]
        else:
            checkout = defaultCheckout
        projects.append(ProjectDesc(p[u'name'], p[u'version'],
                                    overrides=p[u'overrides'],
                                    checkout=checkout))
    return StackDesc(projects)

def main():
    from os.path import join

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s:' + logging.BASIC_FORMAT)

    if len(sys.argv) != 2 or '-h' in sys.argv:
        print "Usage: %s config.json" % sys.argv[0]
        sys.exit(1)

    slot = parseConfigFile(sys.argv[1])

    build_dir = join(os.getcwd(), 'build')
    sources_dir = join(os.getcwd(), 'sources')

    from datetime import datetime
    starttime = datetime.now()

    log.info('Cleaning directories.')
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    if os.path.exists(sources_dir):
        shutil.rmtree(sources_dir)

    log.info('Checking out projects.')
    os.makedirs(build_dir)
    os.makedirs(sources_dir)

    slot.checkout(build_dir)

    for p in slot.projects:
        log.info('Packing %s %s...', p.name, p.version)
        call(['tar', 'cjf', join(sources_dir, p.name + '.src.tar.bz2'),
              p.projectDir], cwd=build_dir)

    log.info('Sources ready for build (time taken: %s).', datetime.now() - starttime)
