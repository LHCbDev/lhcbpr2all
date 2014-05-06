###############################################################################
# (c) Copyright 2014 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
'''

Test for the Manifest parser

Created on Feb 27, 2014

@author: Ben Couturier
'''
import LbUtils.Log
import logging
import os
import unittest
from os.path import normpath, join
from LbTools.Manifest import Parser

class Test(unittest.TestCase):
    ''' Test case of the Manifest parser class '''

    def setUp(self):
        ''' Setup the test '''
        self._data_dir = normpath(join(*([__file__] + [os.pardir] * 4
                                         + ['testdata', 'tools'])))
        self._data_file = join(self._data_dir, "manifest.xml")
        logging.basicConfig()
        LbUtils.Log._default_log_format = '%(asctime)s:' \
                                            + LbUtils.Log._default_log_format

    def tearDown(self):
        ''' Tear down the test '''
        pass

    def testGetProject(self):
        ''' test  loading of project name/version '''
        parser = Parser(self._data_file)
        (p, v) = parser.getProject()
        self.assertEqual(p, 'Brunel', "Project name")
        self.assertEqual(v, 'HEAD', "Project version")

    def testGetHEPTools(self):
        ''' test loading of LCG info '''
        parser = Parser(self._data_file)
        (v, b, l) = parser.getHEPTools()
        self.assertEqual(v, '66', "LCG version")
        self.assertEqual(b, 'x86_64-slc6-gcc48-opt', "CMTCONFIG")
        self.assertEqual(l, 'x86_64-slc6-gcc48', "LCG system")

    def testUsedProjects(self):
        ''' test the getUsedProjects method '''
        parser = Parser(self._data_file)
        usedProjects = parser.getUsedProjects()
        self.assertEqual(len(usedProjects), 2, "Number of used projects")

    def testUsedDataPackages(self):
        ''' test the getUsedDataPackages method '''
        parser = Parser(self._data_file)
        used = parser.getUsedDataPackages()
        self.assertEqual(len(used), 5, "Number of used data packages")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLoadXML']
    unittest.main()