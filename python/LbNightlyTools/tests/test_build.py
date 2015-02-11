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

from os.path import normpath, join


_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

def test_basic_buils():
    with TemporaryDir():
        slot = Slot('test', build_tool='echo')
        slot.projects.append(Project('Gaudi', 'HEAD', checkout='ignore'))
        slot.checkout()
        res = slot.build()
        assert 'Gaudi' in res
        assert res['Gaudi'].returncode == 0
