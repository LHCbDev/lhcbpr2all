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
import json

from LbNightlyTools.tests.utils import processFile

# Uncomment to disable the tests.
#__test__ = False

from LbNightlyTools.Scripts import Preconditions

def test_parseConfigFile():
    'Preconditions.parseConfigFile()'
    expected = [{"name": "waitForFile",
                 "args": {"path": "path/to/file"}}]

    found = processFile(json.dumps({'preconditions': expected}),
                        Preconditions.parseConfigFile)
    assert found == expected

    found = processFile(json.dumps({}),
                        Preconditions.parseConfigFile)
    assert found == []

