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
Module grouping the common build functions.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import logging
from LbNightlyTools.Utils import tee_call

__log__ = logging.getLogger(__name__)


class BuildResults(object):
    '''
    Class used to analyze the build reports of projects.
    '''
    def __init__(self, project, returncode, stdout, stderr):
        '''
        Initialize the instance with raw data from the build.
        '''
        self.project = project
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class make(object):
    '''
    Base class for build tools based on make.
    '''
    def _make(self, target, proj, **kwargs):
        '''
        Internal function to wrap the call to make for CMT.

        @param target: name of the target to build
        @param proj: Project instance to build
        @param jobs: number of parallel build processes [default: 1]
        @param max_load: maximum allowed load beyond which no new process are started
        @param verbose: echo the build output [default: False]
        @param env: dictionary used to override environment variables from the
                    project configuration
        @param args: list of extra arguments to pass to make
        '''
        jobs = kwargs.get('jobs')
        max_load = kwargs.get('max_load')
        verbose = kwargs.get('verbose')

        env = proj.environment()
        env.update(kwargs.get('env', {}))
        # "unset" variables set to None
        env = dict((key, value)
                   for key, value in env.iteritems()
                   if value is not None)

        cmd = ['make']
        if jobs:
            cmd.append('-j%d' % jobs)
        if max_load:
            cmd.append('-l%.1f' % max_load)
        cmd.extend(kwargs.get('args', []))
        cmd.append(target)

        build_root = os.path.join(proj.rootdir, proj.baseDir)

        __log__.debug('running %s', ' '.join(cmd))
        output = tee_call(cmd, env=env, cwd=build_root, verbose=verbose)
        __log__.debug('command exited with code %d', output[0])

        return BuildResults(proj, *output)

    def build(self, proj, **kwargs):
        '''
        Build a project.
        '''
        return self._make('all', proj, **kwargs)

    def clean(self, proj, **kwargs):
        '''
        Clean the build products.
        '''
        return self._make('clean', proj, **kwargs)

    def test(self, proj, **kwargs):
        '''
        Run the tests.
        '''
        return self._make('test', proj, **kwargs)


class cmt(make):
    '''
    Class to wrap the build/test semantics for CMT-based projects.
    '''
    def _make(self, target, proj, **kwargs):
        '''
        Override basic make call to set the environment variable USE_CMT=1.
        '''
        env = kwargs.pop('env', {})
        # PWD and CWD may cause troubles to CMT, so we unset them
        env.update({'USE_CMT': '1',
                    'PWD': None,
                    'CWD': None})
        return make._make(self, target, proj, env=env, **kwargs)

    def clean(self, proj, **kwargs):
        '''
        Override default clean method to call the 'purge' target (more
        aggressive).
        '''
        return self._make('purge', proj, **kwargs)

    def test(self, proj, **kwargs):
        '''
        Run the tests in a Gaudi/LHCb project using CMT.
        '''
        # ensure that tests are not run in parallel
        kwargs.pop('max_load', None)
        kwargs.pop('jobs', None)
        return self._make('test', proj, **kwargs)


class cmake(object):
    '''
    Class to wrap the build/test semantics for CMT-based projects.
    '''
    def _cache_preload_file(self, proj):
        '''
        Name of the cache preload file to be passed to CMake.
        '''
        return os.path.join(proj.roodir, proj.baseDir, 'cache_preload.cmake')

    def _prepare_cache(self, proj, cache_entries=None):
        '''
        Prepare the cache_preload.cmake file passed to CMake during the
        configuration.
        '''
        # prepare the cache to give to CMake: add the launcher rules commands,
        # followed by what is found passed as argument
        if cache_entries is None:
            cache_entries = []
        elif hasattr(cache_entries, 'items'):
            cache_entries = cache_entries.items()

        # add the RULE_LAUNCH settings for the build
        launcher_cmd = 'lbn-wrapcmd <CMAKE_CURRENT_BINARY_DIR> <TARGET_NAME>'
        cache_entries = ([('GAUDI_RULE_LAUNCH_%s' % n, launcher_cmd)
                          for n in ('COMPILE', 'LINK', 'CUSTOM')] +
                         cache_entries)

        with open(self._cache_preload_file(proj), 'w') as cache:
            cache.writelines(['set(%s "%s" CACHE STRING "override")\n' % item
                              for item in cache_entries])

    def _make(self, target, proj, **kwargs):
        '''
        Override basic make call to set the environment variable USE_CMT=1.
        '''
        self._prepare_cache(proj,
                            cache_entries=kwargs.pop('cache_entries', None))

        env = kwargs.pop('env', {})
        env.update({'USE_CMAKE': '1',
                    'USE_MAKE': '1',
                    'CMAKEFLAGS': '-C' + self._cache_preload_file(proj)})
        return make._make(self, target, proj, env=env, **kwargs)

    def build(self, proj, **kwargs):
        '''
        Override the basic build method to call the different targets used in
        CMake builds: configure, all, unasfe-install, post-install.
        '''
        output = [self._make(target, proj, **kwargs)
                  for target in ('configure', 'all',
                                 'unsafe-install', 'post-install')]
        output = (output[1][0], # use the build return code
                  ''.join(step[1] for step in output),
                  ''.join(step[2] for step in output))

        return BuildResults(proj, *output)

    def clean(self, proj, **kwargs):
        '''
        Override default clean method to call the 'purge' target (more
        aggressive).
        '''
        return self._make('purge', proj, **kwargs)

    def test(self, proj, **kwargs):
        '''
        Run the tests in a Gaudi/LHCb project using CMT.
        '''
        # ensure that tests are not run in parallel
        kwargs.pop('max_load')
        kwargs.pop('jobs')
        output = [self._make(target, proj, **kwargs)
                  for target in ('configure', 'test')]
        output = (output[-1][0], # use the test return code
                  ''.join(step[1] for step in output),
                  ''.join(step[2] for step in output))

        return BuildResults(proj, *output)


class no_build(object):
    '''
    No-op build tool, used for projects that do no require a build
    (e.g. projects containing only data packages).
    '''
    def build(self, proj, **kwargs):
        '''
        Build method.
        '''
        return BuildResults(proj, 0, 'no build for %s' % proj, '')

    def clean(self, proj, **kwargs):
        '''
        Clean method.
        '''
        return BuildResults(proj, 0, 'no clean for %s' % proj, '')

    def test(self, proj, **kwargs):
        '''
        Test method.
        '''
        return BuildResults(proj, 0, 'no test for %s' % proj, '')


class echo(object):
    '''
    Dummy build tool class used for testing.
    '''
    def _report(self, target, proj, **kwargs):
        '''
        Helper.
        '''
        output =' '.join([target, str(proj), str(kwargs)])
        print output
        return BuildResults(proj, 0, output, '')

    def build(self, proj, **kwargs):
        '''
        Build method.
        '''
        return self._report('build', proj,**kwargs)

    def clean(self, proj, **kwargs):
        '''
        Clean method.
        '''
        return self._report('clean', proj,**kwargs)

    def test(self, proj, **kwargs):
        '''
        Test method.
        '''
        return self._report('test', proj,**kwargs)


default = cmake


def getMethod(method=None):
    '''
    Helper function to get a build method by name.

    If method is a callable we return it, otherwise we look for the name in the
    current module or as a function coming from another module.
    If method is None, we return the default checkout method.
    '''
    if method is None:
        return default
    if hasattr(method, 'build'):
        return method
    if isinstance(method, basestring):
        if '.' in method:
            # method is a fully qualified function name
            m, f = method.rsplit('.', 1)
            return getattr(__import__(m, fromlist=[f]), f)
        else:
            # it must be a name in this module
            return globals()[method]
