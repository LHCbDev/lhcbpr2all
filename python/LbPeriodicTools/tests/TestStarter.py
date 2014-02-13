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

Test for the PeriodTest Tools

Created on Dec 3, 2013

@author: Ben Couturier
'''
import logging
import json
import os
import unittest
from os.path import normpath, join
from LbPeriodicTools.LbPeriodicStarter import PeriodicTestStarter

class Test(unittest.TestCase):
    ''' Test case of the PeriodicTestStarter class '''

    def setUp(self):
        ''' Setup the test '''
        self._data_dir = normpath(join(*([__file__] + [os.pardir] * 4
                                         + ['testdata', 'periodic_tests'])))
        self._data_file = join(self._data_dir, "starter_schedule.xml")
        self._data_file2 = join(self._data_dir, "test_schedule.xml")
        self._json_file = join(self._data_dir, "slotbuilds.json")
        self._slot_data = None
        with open(self._json_file) as jsonfile:
            self._slot_data = json.load(jsonfile)

        logging.basicConfig(level=logging.INFO)

    def tearDown(self):
        ''' tear down the test '''
        pass

    def testStarter(self):
        '''
        Test the PeriodicTestStarter based
        on the saved JSON file
        '''
        # Create a starter that will date its JSON data
        #from the one we loaded in memory
        starter = PeriodicTestStarter(self._data_file,
                                      "2013-12-02",
                                      86400,
                                      lambda x: self._slot_data)
        all_tests = starter.getAllTests()
        self.assertEqual(len(all_tests[1]), 2,
                         "2 tests templates")

        #0 ==> (u'lhcb-trigger-2011', {u'version': u'v12r8g3',
        # u'name': u'Moore'},
        # u'x86_64-slc5-gcc43-opt')
        #1 ==> (u'lhcb-trigger-2012', {u'version': u'v14r8p3',
        # u'name': u'Moore'},
        # u'x86_64-slc5-gcc43-opt')
        #2 ==> (u'lhcb-trigger-2012', {u'version': u'v14r8p3',
        # u'name': u'Moore'},
        # u'x86_64-slc5-gcc46-opt')
        #3 ==> (u'lhcb-trigger-dev', {u'disabled': True,
        # u'version': u'v20r4', u'name': u'Moore'},
        # u'x86_64-slc5-gcc46-opt')
        #4 ==> (u'lhcb-trigger-dev', {u'version': u'v20r4',
        # u'name': u'MooreOnline'},
        # u'x86_64-slc5-gcc46-opt')
        #5 ==> (u'lhcb-trigger', {u'version': u'v12r9p6',
        # u'name': u'Moore'},
        # u'x86_64-slc5-gcc43-opt')

        for (template, tlist) in all_tests:
            logging.info("Will run the %d tests for template: %s",
                         len(tlist), template)
            if template.slot == 'test-slot':
                self.assertEqual(0, len(tlist), "Number of tests found")
            elif template.slot == 'lhcb-trigger*':
                self.assertEqual(6, len(tlist), "Number of tests found")
            for test_inst in tlist:
                logging.info(test_inst)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLoadXML']
    unittest.main()