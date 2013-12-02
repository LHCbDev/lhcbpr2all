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

__all__ = ('which', 'MockFunc', 'processFile', 'processFileWithName')

def which(cmd):
    '''
    find a command in the path
    '''
    from os.path import join, exists
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
    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

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
    path = tempfile.mkdtemp()
    filepath = os.path.join(path, name)
    f = open(filepath, 'w')
    try:
        f.write(data)
        f.close()
        return function(filepath)
    finally:
        shutil.rmtree(path, ignore_errors=True)
