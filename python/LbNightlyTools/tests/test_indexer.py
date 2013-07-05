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
from os.path import normpath, join

# Uncomment to disable the tests.
#__test__ = False

from LbNightlyTools import Indexer

_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

def test_filesToIndex():
    'Indexer.filesToIndex()'
    files = list(Indexer.filesToIndex(join(_testdata, 'indexer', 'AProject')))

    expected = ['MyPackage/Headers/MyHeader.h',
                'MyPackage/python/MyPackage/SomeModule.py',
                #'MyPackage/python/MyPackage/__init__.py',
                'MyPackage/scripts/MyScript',
                'MyPackage/src/MySource.cpp',
                'InstallArea/include/GeneratedHeader.h',
                #'InstallArea/python/AProject_merged_confDb.py',
                'InstallArea/python/GeneratedPython.py',
                #'InstallArea/python/MyPackage/MyPackageConf.py',
                #'InstallArea/python/MyPackage/MyPackage_confDb.py',
                #'InstallArea/python/MyPackage/MyPackage_user_confDb.py',
                ]

    #from pprint import pprint
    #pprint(files)
    assert files == expected

