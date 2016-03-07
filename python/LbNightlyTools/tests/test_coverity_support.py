###############################################################################
# (c) Copyright 2016 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################

import os
from os.path import join, exists
from subprocess import CalledProcessError

from .utils import TESTDATA_PATH, TemporaryDir

from ..Scripts.Build import Script as Builder

COV_DATA = join(TESTDATA_PATH, 'coverity')

def setup():
    # add to the path the Coverity mock tools
    os.environ['PATH'] = ':'.join([join(COV_DATA, 'bin'),
                                   join(TESTDATA_PATH, '../scripts'),
                                   os.environ['PATH']])
    os.environ['COVERITY_PASSPHRASE'] = 'dummy'

def in_temp_dir(func):
    '''
    Decorator to run a test in a temporary directory.
    '''
    from functools import wraps
    @wraps(func)
    def wrapper():
        with TemporaryDir(chdir=True, skel=COV_DATA):
            return func()
    return wrapper

def run_build(args):
    '''
    Helper to run the build script.
    '''
    rc = Builder().run(args)
    if rc:
        raise CalledProcessError(rc, ['lbn-build'] + args)

@in_temp_dir
def test_analyze():
    run_build(['--coverity', 'test-slot'])
    assert exists(join('TEST', 'TEST_HEAD', 'cov-out'))
