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
import os
import contextlib

from os.path import normpath, join, exists, relpath
from subprocess import Popen, PIPE

import logging
logging.basicConfig(level=logging.FATAL)

# Uncomment to disable the tests.
#__test__ = False

from LbNightlyTools import Utils
from LbNightlyTools.tests.utils import TemporaryDir

_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

def _getfilelist(path, start='.'):
    '''
    Get the list of files and directories in a directory as they are returned
    by 'tar --list' (in arbitrary order).
    '''
    for root, _dirs, files in os.walk(join(start, path), followlinks=True):
        yield relpath(root, start) + '/'
        for filename in files:
            yield relpath(join(root, filename), start)

def test_basic():
    'Utils.pack() basic functionality'
    with TemporaryDir() as tmpdir:
        dest = os.path.join(tmpdir, 'indexer.tar.bz2')
        Utils.pack(['indexer'], dest, cwd=_testdata, checksum='md5')
        assert exists(dest)
        assert exists(dest + '.md5')
        list_tar = Popen(['tar', '--list', '--file', dest], stdout=PIPE)
        out, _ = list_tar.communicate()
        assert list_tar.returncode == 0
        found_files = set(map(str.strip, out.splitlines()))
        expected_files = set(_getfilelist('indexer', _testdata))
        assert expected_files == found_files
        md5sum_check = Popen(['md5sum', '--check',
                              os.path.basename(dest + '.md5')],
                             cwd=os.path.dirname(dest))
        assert md5sum_check.wait() == 0

    with TemporaryDir() as tmpdir:
        dest = os.path.join(tmpdir, 'indexer.tar.bz2')
        Utils.pack(['indexer'], dest, cwd=_testdata)
        assert exists(dest)
        assert not exists(dest + '.md5')
        list_tar = Popen(['tar', '--list', '--file', dest], stdout=PIPE)
        out, _ = list_tar.communicate()
        assert list_tar.returncode == 0
        found_files = set(map(str.strip, out.splitlines()))
        expected_files = set(_getfilelist('indexer', _testdata))
        assert expected_files == found_files

def test_links():
    'Utils.pack() with symbolic links'
    with TemporaryDir() as tmpdir:
        linksdir = os.path.join(tmpdir, 'links')
        os.makedirs(os.path.join(linksdir, 'dir_a'))
        with open(os.path.join(linksdir, 'a.txt'), 'w') as f:
            f.write('test file')
        os.symlink('a.txt', os.path.join(linksdir, 'b.txt'))
        os.symlink(os.path.join(os.pardir, 'a.txt'),
                   os.path.join(linksdir, 'dir_a', 'a.txt'))
        os.symlink('dir_a', os.path.join(linksdir, 'dir_b'))
        os.symlink('no_file', os.path.join(linksdir, 'broken'))

        dest = os.path.join(tmpdir, 'links.tar.bz2')
        Utils.pack(['links'], dest, cwd=tmpdir, checksum='md5')
        assert exists(dest)
        assert exists(dest + '.md5')
        list_tar = Popen(['tar', '--list', '--file', dest], stdout=PIPE)
        out, _ = list_tar.communicate()
        assert list_tar.returncode == 0
        found_files = set(map(str.strip, out.splitlines()))
        expected_files = set(_getfilelist('links', tmpdir))
        expected_files.remove('links/broken')
        assert expected_files == found_files
        md5sum_check = Popen(['md5sum', '--check',
                              os.path.basename(dest + '.md5')],
                             cwd=os.path.dirname(dest))
        assert md5sum_check.wait() == 0

@contextlib.contextmanager
def custom_packcmd(newcmd):
    '''Helper context to replace the packing command in Utils.'''
    old = Utils._packcmd
    Utils._packcmd = newcmd
    yield
    Utils._packcmd = old

@contextlib.contextmanager
def custom_packtestcmd(newcmd):
    '''Helper context to replace the package test command in Utils.'''
    old = Utils._packtestcmd
    Utils._packtestcmd = newcmd
    yield
    Utils._packtestcmd = old

def failer_cmd(src, dest, cwd='.', dereference=True, exclude=None):
    return 1

def test_failing_packer():
    'Utils.pack() failing packer'
    with TemporaryDir() as tmpdir:
        dest = os.path.join(tmpdir, 'indexer.tar.bz2')
        # create an empty file to test the removal of corrupted packages
        open(dest, 'wb').close()
        with custom_packcmd(failer_cmd):
            Utils.pack(['indexer'], dest, cwd=_testdata, checksum='md5')
        assert not exists(dest)
        assert not exists(dest + '.md5')

def test_failing_tester():
    'Utils.pack() failing tester'
    with TemporaryDir() as tmpdir:
        dest = os.path.join(tmpdir, 'indexer.tar.bz2')
        # create an empty file to test the removal of corrupted packages
        open(dest, 'wb').close()
        with custom_packtestcmd(failer_cmd):
            Utils.pack(['indexer'], dest, cwd=_testdata, checksum='md5')
        assert not exists(dest)
        assert not exists(dest + '.md5')
