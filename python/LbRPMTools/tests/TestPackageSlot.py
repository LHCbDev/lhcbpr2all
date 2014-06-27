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

Test for the Tools generating Spec files

Created on Dec 3, 2013

@author: Ben Couturier
'''
import logging
import json
import os
import unittest
from os.path import normpath, join, exists

class Test(unittest.TestCase):
    ''' Test cases for the RPM Spec builder '''

    def setUp(self):
        ''' Setup the test '''
        self._data_dir = normpath(join(*([__file__] + [os.pardir] * 4
                                         + ['testdata', 'rpm'])))

        self._slotconfig = normpath(join(*([__file__] + [os.pardir] * 4
                                                  + ['testdata', 'rpm', 'slot-config.json'])))

        self._manifestxml = normpath(join(*([__file__] + [os.pardir] * 4
                                                  + ['testdata', 'rpm', 'manifest.xml'])))

        self._binspecname = "Brunel_v46r0_x86_64-slc6-gcc48-opt.spec"
        self._fullbinspecname =  normpath(join(*([__file__] + [os.pardir] * 4
                                                  + ['testdata', 'rpm', self._binspecname])))
        self._sharedspecname = "Brunel_v46r0.spec"
        self._fullsharedspecname =  normpath(join(*([__file__] + [os.pardir] * 4
                                                  + ['testdata', 'rpm', self._sharedspecname])))

        self._indexspecname = "glimpse_Brunel_v46r0.spec"
        self._fullindexspecname =  normpath(join(*([__file__] + [os.pardir] * 4
                                                  + ['testdata', 'rpm', self._indexspecname])))

        logging.basicConfig(level=logging.INFO)

    def tearDown(self):
        ''' tear down the test '''
        pass

    def testBinarySpec(self):
        '''
        Test the creation of Binary RPMs by the PackageSlot script
        '''

        from tempfile import mkdtemp
        from LbRPMTools.PackageSlot import Script
        artifactdir = mkdtemp()
        script = Script()
        script.run(['--dry-run', '--verbose',  '--build-id', 'lhcb-release.999',
                             '--artifacts-dir',  artifactdir, '--manifest', self._manifestxml,
                             self._slotconfig, '--platform',  'x86_64-slc6-gcc48-opt' ])


        newspecfilename = os.path.join(artifactdir, self._binspecname)
        newlines = [ l for l in open(newspecfilename, 'U').readlines()
                     if "%define buildarea" not in l ]
        oldlines = [ l for l in open(self._fullbinspecname, 'U').readlines()
        if "%define buildarea" not in l ]

        from difflib import Differ, unified_diff
        d = Differ()
        #        result = list(d.compare(oldlines, newlines))
        result = unified_diff(oldlines, newlines, fromfile=self._fullbinspecname,
        tofile=newspecfilename, n=0)
        diffFound = False
        import sys
        for l in result:
            diffFound = True
            sys.stdout.write(l)

        self.assertFalse(diffFound)

        import shutil
        shutil.rmtree(artifactdir)


    def testSharedSpec(self):
        '''
        Test the creation of shared RPMs by the PackageSlot script
        '''

        from tempfile import mkdtemp
        from LbRPMTools.PackageSlot import Script
        artifactdir = mkdtemp()
        script = Script()
        script.run(['--dry-run', '--shared', '--verbose',  '--build-id', 'lhcb-release.999',
                             '--artifacts-dir',  artifactdir, '--manifest', self._manifestxml,
                             self._slotconfig ])


        newspecfilename = os.path.join(artifactdir, self._sharedspecname)
        newlines = [ l for l in open(newspecfilename, 'U').readlines()
                     if "%define buildarea" not in l ]
        oldlines = [ l for l in open(self._fullsharedspecname, 'U').readlines()
        if "%define buildarea" not in l ]

        from difflib import Differ, unified_diff
        d = Differ()
        #        result = list(d.compare(oldlines, newlines))
        result = unified_diff(oldlines, newlines, fromfile=self._fullbinspecname,
        tofile=newspecfilename, n=0)
        diffFound = False
        import sys
        for l in result:
            diffFound = True
            sys.stdout.write(l)

        self.assertFalse(diffFound)

        import shutil
        shutil.rmtree(artifactdir)

    def testGlimpseSpec(self):
        '''
        Test the creation of Glimpse RPMs by the PackageSlot script
        '''

        from tempfile import mkdtemp
        from LbRPMTools.PackageSlot import Script
        artifactdir = mkdtemp()
        script = Script()
        script.run(['--dry-run', '--glimpse', '--verbose',  '--build-id', 'lhcb-release.999',
                             '--artifacts-dir',  artifactdir, '--manifest', self._manifestxml ,
                             self._slotconfig ])


        newspecfilename = os.path.join(artifactdir, self._indexspecname)
        newlines = [ l for l in open(newspecfilename, 'U').readlines()
                     if "%define buildarea" not in l ]
        oldlines = [ l for l in open(self._fullindexspecname, 'U').readlines()
        if "%define buildarea" not in l ]

        from difflib import Differ, unified_diff
        d = Differ()
        #        result = list(d.compare(oldlines, newlines))
        result = unified_diff(oldlines, newlines, fromfile=self._fullindexspecname,
        tofile=newspecfilename, n=0)
        diffFound = False
        import sys
        for l in result:
            diffFound = True
            sys.stdout.write(l)

        self.assertFalse(diffFound)

        import shutil
        shutil.rmtree(artifactdir)


if __name__ == "__main__":
    unittest.main()
