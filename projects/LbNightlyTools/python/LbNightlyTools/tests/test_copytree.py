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
from os import makedirs, readlink, listdir
from os.path import isdir, islink, realpath, join, basename

from LbNightlyTools.tests.utils import TemporaryDir
from LbNightlyTools.Utils import shallow_copytree

def test_no_dst():
    with TemporaryDir(chdir=True):
        for i in range(3):
            makedirs(join('src', 'a', str(i)))
        shallow_copytree('src', 'dst')
        assert islink('dst')
        assert realpath('src') == realpath('dst')
        assert realpath('src') == readlink('dst')

def test_recursion():
    with TemporaryDir(chdir=True):
        for i in range(3):
            makedirs(join('src', 'a', str(i)))
            makedirs(join('src', 'b', str(i)))
        makedirs(join('dst', 'b'))

        shallow_copytree('src', 'dst')

        assert isdir('dst') and not islink('dst')
        assert set(listdir('src')) == set(listdir('dst'))

        assert realpath(join('src', 'a')) == realpath(join('dst', 'a'))
        assert realpath(join('src', 'a')) == readlink(join('dst', 'a'))

        src_b = join('src', 'b')
        dst_b = join('dst', 'b')
        assert isdir(dst_b) and not islink(dst_b)
        assert set(listdir(src_b)) == set(listdir(dst_b))

        for n in [n for n in listdir(src_b) if n not in ('.', '..')]:
            assert realpath(join(src_b, n)) == realpath(join(dst_b, n))
            assert realpath(join(src_b, n)) == readlink(join(dst_b, n))

def test_ignore():
    with TemporaryDir(chdir=True):
        for i in range(3):
            makedirs(join('src', 'a', str(i)))
            makedirs(join('src', 'b', str(i)))
        makedirs(join('dst', 'b'))

        shallow_copytree('src', 'dst',
                         ignore=lambda src, names: ([]
                                                    if basename(src) != 'b'
                                                    else ['1']))

        assert isdir('dst') and not islink('dst')
        assert set(listdir('src')) == set(listdir('dst'))

        assert realpath(join('src', 'a')) == realpath(join('dst', 'a'))
        assert realpath(join('src', 'a')) == readlink(join('dst', 'a'))

        src_b = join('src', 'b')
        dst_b = join('dst', 'b')
        assert isdir(dst_b) and not islink(dst_b)
        assert (set(listdir(src_b)) - set(listdir(dst_b))) == set(['1'])

        for n in [n for n in listdir(src_b) if n not in ('.', '..', '1')]:
            assert realpath(join(src_b, n)) == realpath(join(dst_b, n))
            assert realpath(join(src_b, n)) == readlink(join(dst_b, n))
