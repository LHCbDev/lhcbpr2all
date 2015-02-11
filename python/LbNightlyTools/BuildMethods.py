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

import sys
import os
import select
import errno
import logging
from subprocess import Popen, PIPE

__log__ = logging.getLogger(__name__)

def call(*args, **kwargs):
    '''
    Wrapper for Popen to run a command and collect the output.

    The arguments are those of Popen, with the addition of
    @param verbose: if True, the output and error are printed while the process
                    is running.

    @return: tuple with return code, stdout and stderr

    Example:
    >>> call(['echo hello'], shell=True, verbose=True)
    hello
    (0, 'hello\\n', '')
    '''
    verbose = kwargs.pop('verbose', False)
    if 'stdout' not in kwargs:
        kwargs['stdout'] = PIPE
    if 'stderr' not in kwargs:
        kwargs['stderr'] = PIPE

    proc = Popen(*args, **kwargs)

    if not verbose:
        out, err = proc.communicate()
        retcode = proc.returncode
    else:
        # code inspired (mostly copied) from subprocess module
        poller = select.poll()
        files = {proc.stdout.fileno(): (proc.stdout, sys.stdout),
                 proc.stderr.fileno(): (proc.stderr, sys.stderr)}
        out = []
        err = []
        output = {proc.stdout.fileno(): out,
                  proc.stderr.fileno(): err}

        select_POLLIN_POLLPRI = select.POLLIN | select.POLLPRI

        poller.register(proc.stdout, select_POLLIN_POLLPRI)
        poller.register(proc.stderr, select_POLLIN_POLLPRI)

        def close_unregister_and_remove(fd):
            poller.unregister(fd)
            files[fd][0].close()
            files.pop(fd)

        while files:
            try:
                ready = poller.poll()
            except select.error, e:
                if e.args[0] == errno.EINTR:
                    continue
                raise
            for fd, mode in ready:
                if mode & select_POLLIN_POLLPRI:
                    data = os.read(fd, 4096)
                    if not data:
                        close_unregister_and_remove(fd)
                    output[fd].append(data)
                    files[fd][1].write(data)
                else:
                    # Ignore hang up or errors.
                    close_unregister_and_remove(fd)
        out = ''.join(out)
        err = ''.join(err)
        retcode = proc.wait()

    return retcode, out, err


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

def cmt(proj, *args, **kwargs):
    '''
    Build a Gaudi/LHCb project using CMT.
    '''
    jobs = kwargs.get('jobs', 1)
    verbose = kwargs.get('verbose')

    env = proj.environment()
    env['USE_CMT'] = '1'

    cmd = ['make', '-j%d' % jobs]
    cmd.extend(kwargs.get('args', []))
    if args:
        cmd.extend(args)
    build_root = os.path.join(proj.rootdir, proj.baseDir)

    __log__.debug('running %s', ' '.join(cmd))
    output = call(cmd, env=env, cwd=build_root, verbose=verbose)
    __log__.debug('command exited with code %d', output[0])

    return BuildResults(proj, *output)

def cmake(proj, *args, **kwargs):
    '''
    Build a Gaudi/LHCb project using CMake.
    '''
    jobs = kwargs.get('jobs', 1)
    verbose = kwargs.get('verbose')
    max_load = kwargs.get('max_load')

    env = proj.environment()
    env['USE_CMAKE'] = '1'
    env['USE_MAKE'] = '1' # this is to avoid ninja for the build

    cmd = ['make', '-j%d' % jobs]
    if max_load:
        cmd.append('-l%.1f' % max_load)
    cmd.extend(kwargs.get('args', []))
    build_root = os.path.join(proj.rootdir, proj.baseDir)

    if args:
        cmd.extend(args)
        __log__.debug('running %s', ' '.join(cmd))
        output = call(cmd, env=env, cwd=build_root, verbose=verbose)
        __log__.debug('command exited with code %d', output[0])
    else:
        output = []
        for target in ('configure', 'all', 'unsafe-install', 'post-install'):
            cmdtgt = cmd + [target]
            __log__.debug('running: %s', ' '.join(cmdtgt))
            output.append(call(cmdtgt, env=env, cwd=build_root,
                               verbose=verbose))
            __log__.debug('command exited with code %d', output[-1][0])
        output = (output[1][0], # use the build return code
                  ''.join(step[1] for step in output),
                  ''.join(step[2] for step in output))

    return BuildResults(proj, *output)

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
    if hasattr(method, '__call__'):
        return method
    if isinstance(method, basestring):
        if '.' in method:
            # method is a fully qualified function name
            m, f = method.rsplit('.', 1)
            return getattr(__import__(m, fromlist=[f]), f)
        else:
            # it must be a name in this module
            return globals()[method]
