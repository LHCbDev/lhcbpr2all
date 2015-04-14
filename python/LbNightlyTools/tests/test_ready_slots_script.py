##############################################################################
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
__author__ = 'Colas Pomies <colas.pomies@cern.ch>'

from LbNightlyTools import CheckReadySlots

import os
import re
from sets import Set

from os.path import normpath, join
from LbNightlyTools.tests.utils import TemporaryDir

_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

_env_bk = dict(os.environ)

def setup():
    global _env_bk
    _env_bk = dict(os.environ)

def teardown():
    global _env_bk
    os.environ.clear()
    os.environ.update(_env_bk)

def test_no_data():
    with TemporaryDir(chdir=True):
        retval = CheckReadySlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 0

def test_no_file_xml():
    with TemporaryDir(chdir=True):
        slots = CheckReadySlots.Script().extractFromXml('configuration.xml')
        assert len(slots) == 0

def test_no_file_json():
    with TemporaryDir(chdir=True):
        slots = CheckReadySlots.Script().extractFromXml('lhcb-*.json')
        assert len(slots) == 0

def test_no_slot_to_write():
    with TemporaryDir(chdir=True):
        CheckReadySlots.Script().writeFiles(Set(), 'slot-param-{0}.txt')
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 0

