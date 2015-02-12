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
# Uncomment to disable the tests.
#__test__ = False

import os

from LbNightlyTools.Configuration import Slot, Project

from LbNightlyTools.tests.utils import TemporaryDir

from os.path import normpath, join, exists


_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

def test_basic_build():
    with TemporaryDir():
        slot = Slot('slot', build_tool='echo')
        slot.projects.append(Project('Gaudi', 'HEAD', checkout='ignore'))
        slot.checkout()

        res = slot.clean()
        assert 'Gaudi' in res
        assert res['Gaudi'].returncode == 0
        assert 'clean' in res['Gaudi'].stdout

        res = slot.build()
        assert 'Gaudi' in res
        assert res['Gaudi'].returncode == 0
        assert 'build' in res['Gaudi'].stdout

        res = slot.test()
        assert 'Gaudi' in res
        assert res['Gaudi'].returncode == 0
        assert 'test' in res['Gaudi'].stdout

def test_make_build():
    dummy_src = join(_testdata, 'build_tests', 'orig', 'dummy', '.')
    with TemporaryDir(chdir=True):
        slot = Slot('slot', build_tool='make',
                    projects=[Project('dummy', 'head',
                                      checkout='copy',
                                      checkout_opts=dict(src=dummy_src))])
        slot.checkout()
        assert exists(join('DUMMY', 'DUMMY_HEAD', 'Makefile'))

        res = slot.build()
        assert 'dummy' in res
        assert '=== building all ===' in res['dummy'].stdout
        assert exists(join('DUMMY', 'DUMMY_HEAD', 'all'))

        res = slot.test()
        assert 'dummy' in res
        assert '=== running tests ===' in res['dummy'].stdout
        assert exists(join('DUMMY', 'DUMMY_HEAD', 'test_results'))

        res = slot.clean()
        assert 'dummy' in res
        assert '=== cleaning ===' in res['dummy'].stdout
        assert exists(join('DUMMY', 'DUMMY_HEAD', 'Makefile'))
        assert not exists(join('DUMMY', 'DUMMY_HEAD', 'all'))
        assert not exists(join('DUMMY', 'DUMMY_HEAD', 'test_results'))
