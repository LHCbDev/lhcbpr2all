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
from datetime import datetime
from LbNightlyTools.Utils import log_call as _log_call


__log__ = logging.getLogger(__name__)
__log__.setLevel(logging.DEBUG)

def log_call(*args, **kwargs):
    '''
    Helper to send log messages of log_call to __log__ by default.
    '''
    if 'logger' not in kwargs:
        kwargs['logger'] = __log__.getChild(args[0][0].replace('.', '_'))
    return _log_call(*args, **kwargs)


def ensure_dir(path):
    '''
    Make sure that a directory exist, creating it and printing a warning if not.
    '''
    if not os.path.exists(path):
        __log__.warning('directory %s is missing, I create it', path)
        os.makedirs(path)


class BuildResults(object):
    '''
    Class used to analyze the build reports of projects.
    '''
    def __init__(self, project, returncode, stdout, stderr,
                 started, completed=None):
        '''
        Initialize the instance with raw data from the build.
        '''
        self.project = project
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.started = started
        self.completed = completed or datetime.now()


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
        @param env: dictionary used to override environment variables from the
                    project configuration
        @param args: list of extra arguments to pass to make
        '''
        jobs = kwargs.get('jobs')
        max_load = kwargs.get('max_load')

        env = proj.environment()
        env.update(kwargs.get('env', {}))
        # "unset" variables set to None
        env = dict((key, value)
                   for key, value in env.iteritems()
                   if value is not None)

        cmd_kwargs = {'env': env,
                      'cwd': proj.baseDir}
        if 'stderr' in kwargs:
            cmd_kwargs['stderr'] = kwargs['stderr']

        cmd = ['make']
        if jobs:
            cmd.append('-j%d' % jobs)
        if max_load:
            cmd.append('-l%.1f' % max_load)
        cmd.extend(kwargs.get('args', []))
        cmd.append(target)

        ensure_dir(cmd_kwargs['cwd'])

        __log__.debug('running %s', ' '.join(cmd))
        started = datetime.now()
        retcode, out, err = log_call(cmd, **cmd_kwargs)
        completed = datetime.now()
        __log__.debug('command exited with code %d', retcode)

        out = ('#### {0} {1} ####\n'
               '# Start: {2}\n{3}'
               '# End: {4}\n').format(self,
                                      target,
                                      started.isoformat(),
                                      out,
                                      completed.isoformat())
        return BuildResults(proj, retcode, out, err, started, completed)

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

    def __str__(self):
        '''
        Conversion to string.
        '''
        return 'make'


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
        env = kwargs.get('env', {})
        if 'CMTCONFIG' not in env:
            env['CMTCONFIG'] = os.environ.get('CMTCONFIG')
        if 'GAUDI_QMTEST_HTML_OUTPUT' not in env:
            bin_dir = os.path.join(os.path.abspath(proj.baseDir),
                                   'build.{CMTCONFIG}'.format(**env),
                                   'html')
            env['GAUDI_QMTEST_HTML_OUTPUT'] = bin_dir
        kwargs['env'] = env
        return self._make('test', proj, **kwargs)

    def __str__(self):
        '''
        Conversion to string.
        '''
        return 'CMT'


class cmake(make):
    '''
    Class to wrap the build/test semantics for CMT-based projects.
    '''
    def _cache_preload_file(self, proj):
        '''
        Name of the cache preload file to be passed to CMake.
        '''
        return os.path.join(proj.baseDir, 'cache_preload.cmake')

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

        cache_file = self._cache_preload_file(proj)
        ensure_dir(os.path.dirname(cache_file))
        with open(cache_file, 'w') as cache:
            cache.writelines(['set(%s "%s" CACHE STRING "override")\n' % item
                              for item in cache_entries])

    def _make(self, target, proj, **kwargs):
        '''
        Override basic make call to set the environment variable USE_CMT=1.
        '''
        self._prepare_cache(proj,
                            cache_entries=kwargs.pop('cache_entries', None))

        env = kwargs.pop('env', {})
        preload_file = os.path.join(os.getcwd(), self._cache_preload_file(proj))
        env.update({'USE_CMAKE': '1',
                    'USE_MAKE': '1',
                    'CMAKEFLAGS': '-C' + preload_file})
        return make._make(self, target, proj, env=env, **kwargs)

    def build(self, proj, **kwargs):
        '''
        Override the basic build method to call the different targets used in
        CMake builds: configure, all, unasfe-install, post-install.
        '''
        output = [self._make(target, proj, **kwargs)
                  for target in ('configure', 'all',
                                 'unsafe-install', 'post-install')]

        output = (output[1].returncode, # use the build return code
                  ''.join(step.stdout for step in output),
                  ''.join(step.stderr for step in output),
                  output[0].started,
                  output[-1].completed)

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
        kwargs.pop('max_load', None)
        kwargs.pop('jobs', None)
        output = [self._make(target, proj, **kwargs)
                  for target in ('configure', 'test')]
        output = (output[-1].returncode, # use the test return code
                  ''.join(step.stdout for step in output),
                  ''.join(step.stderr for step in output),
                  output[0].started,
                  output[-1].completed)

        return BuildResults(proj, *output)

    def __str__(self):
        '''
        Conversion to string.
        '''
        return 'CMake'


class no_build(object):
    '''
    No-op build tool, used for projects that do no require a build
    (e.g. projects containing only data packages).
    '''
    def build(self, proj, **kwargs):
        '''
        Build method.
        '''
        __log__.debug('no build for %s', proj)
        return BuildResults(proj, 0, 'no build for %s' % proj,
                            '', datetime.now())

    def clean(self, proj, **kwargs):
        '''
        Clean method.
        '''
        __log__.debug('no clean for %s', proj)
        return BuildResults(proj, 0, 'no clean for %s' % proj,
                            '', datetime.now())

    def test(self, proj, **kwargs):
        '''
        Test method.
        '''
        __log__.debug('no test for %s', proj)
        return BuildResults(proj, 0, 'no test for %s' % proj,
                            '', datetime.now())

    def __str__(self):
        '''
        Conversion to string.
        '''
        return 'no-build'

class echo(object):
    '''
    Dummy build tool class used for testing.
    '''
    def _report(self, target, proj, **kwargs):
        '''
        Helper.
        '''
        output = ' '.join([target, str(proj), str(kwargs)])
        __log__.debug(output)
        return BuildResults(proj, 0, output,
                            '', datetime.now())

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

    def __str__(self):
        '''
        Conversion to string.
        '''
        return 'echo'


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
