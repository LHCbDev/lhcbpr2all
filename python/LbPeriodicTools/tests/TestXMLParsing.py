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
import LbUtils.Log
import logging
import os
import unittest
from os.path import normpath, join
from LbPeriodicTools.LbPeriodicTestSchedule import PeriodicTestSchedule

class Test(unittest.TestCase):
    ''' Test case of the LbPeriodicTestSchedule class '''

    def setUp(self):
        ''' Setup the test '''
        self._data_dir = normpath(join(*([__file__] + [os.pardir] * 4
                                         + ['testdata', 'periodic_tests'])))
        self._data_file = join(self._data_dir, "schedule.xml")
        self._data_file_nok = join(self._data_dir, "scheduleIncorrect.xml")
        logging.basicConfig()
        LbUtils.Log._default_log_format = '%(asctime)s:' \
                                            + LbUtils.Log._default_log_format

    def tearDown(self):
        ''' Tear down the test '''
        pass

    def testLoadTestXMLFile(self):
        ''' test the actual XML loading '''
        schedule = PeriodicTestSchedule(self._data_file)
        # Checking the count when loading all
        self.assertEqual(len(schedule.getTests()), 2,
                         "Number of tests in test file")

    def testFilterResults(self):
        ''' test the filtering of the results '''
        schedule = PeriodicTestSchedule(self._data_file)
        # looking for Brunel tests
        btests = schedule.getTests(lambda t: t.project.lower() == "brunel")
        self.assertEqual(len(btests), 1, "Number of Brunel tests in test file")
        self.assertEqual(btests[0].project, "Brunel", "Test loaded correctly")

    def testSchedCheck(self):
        ''' Check that an exception is thrown in case of bad date '''
        self.assertRaises(ValueError, PeriodicTestSchedule,
                          self._data_file_nok, True)

    def testScheduleType(self):
        ''' test the filtering of the results '''
        schedule = PeriodicTestSchedule(self._data_file)
        # looking for Brunel tests
        btests = schedule.getTests(lambda t: t.project.lower() == "brunel")
        self.assertEqual(btests[0].scheduletype, "month",
                         "Monthly Brunel Schedule")
        bproj = schedule.getTests(lambda t: t.project.lower() == "project")
        self.assertEqual(bproj[0].scheduletype, "week",
                         "Weekly Brunel Schedule")

    def testScheduleTime(self):
        ''' test the filtering of the results '''
        schedule = PeriodicTestSchedule(self._data_file)
        # looking for Brunel tests
        btests = schedule.getTests(lambda t: t.project.lower() == "brunel")
        self.assertEqual(btests[0].scheduletime, "12:00", "Job time")

    def testRunCount(self):
        ''' test if the count is set '''
        schedule = PeriodicTestSchedule(self._data_file)
        # looking for Brunel tests
        btests = schedule.getTests(lambda t: t.project.lower() == "brunel")
        self.assertEqual(btests[0].count, 30, "Number of runs")
        bproj = schedule.getTests(lambda t: t.project.lower() == "project")
        self.assertEqual(bproj[0].count, 1, "Number of runs")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLoadXML']
    unittest.main()