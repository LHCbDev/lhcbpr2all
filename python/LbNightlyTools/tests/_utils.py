'''
Utility functions used for testing.
'''
import os
import tempfile

__all__ = ('which', 'MockFunc', 'processFile')

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
    fd, path = tempfile.mkstemp()
    f = os.fdopen(fd, 'w')
    try:
        f.write(data)
        f.close()
        return function(path)
    finally:
        os.remove(path)
