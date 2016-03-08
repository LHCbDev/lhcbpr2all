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
Utility functions used for testing.
'''
import os
import shutil
import tempfile
import logging
from os.path import normpath, join, exists

__all__ = ('which', 'MockFunc', 'processFile', 'processFileWithName',
           'MockLoggingHandler', 'TemporaryDir', 'TESTDATA_PATH')

TESTDATA_PATH = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

def which(cmd):
    '''
    find a command in the path
    '''
    try:
        return (join(d, cmd)
                for d in os.environ['PATH'].split(os.pathsep)
                if exists(join(d, cmd))).next()
    except StopIteration:
        return None

class MockFunc(object):
    '''
    Helper class to record the arguments a callback is called with.
    '''
    def __init__(self):
        self.args = None
        self.kwargs = None
        self.__name__ = 'mock'
    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class TemporaryDir(object):
    '''
    Helper class to create a temporary directory and manage its lifetime.

    An instance of this class can be used inside the 'with' statement and
    returns the path to the temporary directory.
    '''
    def __init__(self, chdir=False, keep=False, skel=None):
        '''Constructor.

        @param chdir: change to the temporary directory while inside the context
        @param keep: do not delete the temporary directory once out of context
        @param skel: fill the temporary directory with the content of the
                     provided directory
        '''
        self.chdir = chdir
        self.keep = keep
        self.path = tempfile.mkdtemp()
        self.old_dir = None
        if skel:
            for src, _dirs, files in os.walk(skel):
                dst = join(self.path, os.path.relpath(src, skel))
                if not os.path.exists(dst):
                    os.makedirs(dst)
                    shutil.copymode(src, dst)
                for f in [join(src, f) for f in files]:
                    shutil.copy(f, dst)

    def join(self, *args):
        '''
        Equivalent to os.path.join(self.path, *args).
        '''
        return os.path.join(self.path, *args)
    def __str__(self):
        '''String representation (path to the temporary directory).'''
        return self.path
    def remove(self):
        '''
        Remove the temporary directory.
        After a call to this method, the object is not usable anymore.
        '''
        if self.path: # allow multiple calls to the remove method
            shutil.rmtree(self.path, ignore_errors=True)
            self.path = None
    def __enter__(self):
        '''
        Context Manager protocol 'enter' function.
        '''
        if self.chdir:
            self.old_dir = os.getcwd()
            os.chdir(self.path)
        return self.path
    def __exit__(self, exc_type, exc_val, exc_tb):
        '''
        Context Manager protocol 'exit' function.
        Remove the temporary directory and let the exceptions propagate.
        '''
        if self.old_dir:
            os.chdir(self.old_dir)
            self.old_dir = None
        if not self.keep:
            self.remove()
        else:
            print "WARNING: not removing temporary directory", self.path
        return False

def processFile(data, function):
    '''
    Process the string data via the function 'function' that accepts a filename
    as parameter.
    '''
    fdesc, path = tempfile.mkstemp()
    f = os.fdopen(fdesc, 'w')
    try:
        f.write(data)
        f.close()
        return function(path)
    finally:
        os.remove(path)

def processFileWithName(data, name, function):
    '''
    Process the string data via the function 'function' that accepts a filename
    as parameter, using the given name for the file.
    '''
    with TemporaryDir() as path:
        filepath = os.path.join(path, name)
        with open(filepath, 'w') as f:
            f.write(data)
        return function(filepath)

# Code taken from http://stackoverflow.com/a/1049375/576333
class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs.
    To use it:
    >>> mlh = MockLoggingHandler()
    >>> logging.getLogger().addHandler(mlh)
    >>> logging.debug('hello')
    >>> mlh.messages['debug']
    ['hello']
    """

    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }
