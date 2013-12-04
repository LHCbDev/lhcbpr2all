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
Class to start the periodic tests for a given Date

Created on Dec 2, 2013

@author: Ben Couturier
'''
import logging
from datetime import datetime, timedelta
from LbPeriodicTools.LbPeriodicTestSchedule import PeriodicTestSchedule
from LbNightlyTools.Utils import DAY_NAMES
from LbNightlyTools.Utils import Dashboard

__log__ = logging.getLogger(__name__)

def getSlotsForDay(datestr):
    '''
    Query the test DB to locate the list of slots built
    '''
    dashboard = Dashboard()
    allslots = dashboard.slotsByDay(datestr, datestr, True)
    return allslots

class PeriodicTestStarter (object):
    '''
    Parser to the periodic test scheduling XML file
    '''
    def __init__(self, schedule_filename, datetimestr=None,
                 testperiod=60,
                 get_slot_data=getSlotsForDay):
        '''
        Constructor that takes the XML filename and the test date
        '''
        # Checking date
        if (datetimestr != None):
            self._testdatetimestr = datetimestr
            try:
                self._testdatetime =  datetime.strptime(datetimestr,
                                                        '%Y-%m-%d %H:%M:%S')
            except ValueError:
                self._testdatetime =  datetime.strptime(datetimestr, '%Y-%m-%d')
        else:
            self._testdatetime = datetime.today()


        self._dashboard_date = self._testdatetime.strftime('%Y-%m-%d')
        self._testdatetime_end = self._testdatetime \
                                + timedelta(seconds=testperiod)

        self._testdaynum = self._testdatetime.weekday()
        self._testdaystr = DAY_NAMES[self._testdaynum]

        __log__.info("Looking for tests to between %s and %s"
                     % (self._testdatetime.strftime('%Y-%m-%d %H:%M:%S'),
                        self._testdatetime_end.strftime('%Y-%m-%d %H:%M:%S')))

        # Load the XML file
        alltests = PeriodicTestSchedule(schedule_filename)

        # Select the tests to be run at the date
        to_run = alltests.getTests(lambda x:
                                   x.isForDate(self._testdatetime,
                                               self._testdatetime_end))
        __log__.info("Found %d tests schedule to be run." % len(to_run))
        for test in to_run:
            __log__.info(str(test))

        self._test_schedule = alltests
        self._tests_to_run = to_run
        self._slot_list = get_slot_data(self._dashboard_date)
        self._all_tests = []
        self._createAllTest()

    def getSlotData(self):
        ''' Just returns the build information available to the starter'''
        return self._slot_list

    def _createAllTest(self):
        '''
        Based on the tests templates, performs the globbing on
        the slot-name, project, cmtconfig
        '''
        all_tests = []
        for to_run in self._tests_to_run:
            all_tests.append((to_run, to_run.getBuildMatches(self._slot_list)))

        self._all_tests = all_tests

    def getAllTests(self):
        ''' Just returns complete list of tests identified'''
        return self._all_tests
