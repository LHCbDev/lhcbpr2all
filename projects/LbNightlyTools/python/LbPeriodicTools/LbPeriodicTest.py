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
Class to parse the test Schedule XML file
Created on Dec 2, 2013

@author: Ben Couturier
'''

from fnmatch import fnmatch
from datetime import datetime
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import tostring

from LbNightlyTools.Utils import DAY_NAMES
import logging

__log__ = logging.getLogger(__name__)

ASCHED = "schedule"
ASCHEDTYPE = "scheduletype"
ASCHEDTIME = "scheduletime"
ADSLOT = "slot"
APROJECT = "project"
APLATFORM = "platform"
ATEST = "test"
ATESTGROUP = "testgroup"
ATESTRUNNER = "testrunner"
ATESTENV = "testenv"
ATAG = "os_label"
ADATES = "dates"
ABUILDID = "build_id"
AHOUR = "testhour"
AMINUTE = "testminute"
ACOUNT = "count"

SCHED_TYPE_WEEK = "week"
SCHED_TYPE_MONTH = "month"
TIME_DEFAULT = "19:00"

TEST_ATTRIBUTES = [ ASCHED, ADSLOT, APROJECT, APLATFORM,
                   ATESTGROUP, ATESTRUNNER, ATAG, ATEST, ACOUNT ]
MANDATORY_ATTRIBUTES = [ ASCHED, ADSLOT, APROJECT, APLATFORM, ATESTGROUP ]
SCHED_ATTRIBUTES = [ ABUILDID, ADSLOT, APROJECT, APLATFORM,
                    ATESTGROUP, ATESTRUNNER, ATAG, ATESTENV, ACOUNT ]

def validateDaysOfWeek(daysstr):
    '''
    Validate the schedule.
    Comma separated list of days for the moment
    '''
    sched_days = set([d.strip() for d in daysstr.split(",")])
    unknown_days = sched_days - set(DAY_NAMES)

    if len(unknown_days) > 0:
        raise ValueError("Unknown days in schedule: %s"
                         % ",".join(unknown_days))

def validateDaysOfMonth(daysstr):
    '''
    Validate the schedule.
    Comma separated list of numbers for the moment
    '''
    sched_days = set([int(d.strip()) for d in daysstr.split(",")])
    incorrect_days = [ d for d in sched_days if d <= 0]
    incorrect_days += [ d for d in sched_days if d > 31]
    if len(incorrect_days) > 0:
        raise ValueError("Days have to be between 1 and 31. Not allowed: %s"
                         % ",".join(incorrect_days))

def validateTime(timestr):
    '''
    Validate the time specified for the job
    '''
    mytime = None
    try:
        mytime = datetime.strptime(timestr, '%H:%M:%S')
    except ValueError:
        mytime = datetime.strptime(timestr, '%H:%M')
    return mytime

def _fromXML(etree):
    '''
    Parse a specific periodic test and returns a dictionary with
    all values included
    '''
    if type(etree) != ElementTree and etree.tag != "periodictest":
        raise Exception("Bad tag: this only parses a <periodictest>")

    # Creating and filling the dictionary
    testdict = {}
    attlist = set(TEST_ATTRIBUTES)
    for att in attlist - set([ ATESTGROUP]):
        elem = etree.find(att)
        if elem != None:
            testdict[att] = elem.text
            if (att == ASCHED):
                if "type" in elem.attrib.keys():
                    testdict[ASCHEDTYPE] = elem.attrib["type"].lower()
                if "time" in elem.attrib.keys():
                    testdict[ASCHEDTIME] = elem.attrib["time"].lower()

    # Default to weekly schedule
    if ASCHEDTYPE not in testdict.keys():
        testdict[ASCHEDTYPE] = SCHED_TYPE_WEEK

    # Default the time to 19:00
    if ASCHEDTIME not in testdict.keys():
        testdict[ASCHEDTIME] = TIME_DEFAULT

    # Now processing the testgroup
    elem = etree.find(ATEST)
    if elem == None:
        raise Exception("Missing <test> with test definition in %s"
                        % tostring(etree))
    # And checking the attributes
    for name, value in elem.attrib.items():
        testdict["test" + name] = value

    # Checking if any data is missing
    missing = set(MANDATORY_ATTRIBUTES) - set(testdict.keys())
    if len(missing) >0:
        raise Exception("Missing values for: %s in \n%s"
                        % ((",".join(missing)),tostring(etree)))

    # Checking for unknown attributes
    extra = set([child.tag for child in etree ]) - attlist
    if len(extra) >0:
        raise Exception("Unknown attribute(s): %s in \n%s"
                        % ((",".join(extra)),tostring(etree)))

    if testdict[ASCHEDTYPE] == SCHED_TYPE_WEEK:
        validateDaysOfWeek(testdict[ASCHED])
    if testdict[ASCHEDTYPE] == SCHED_TYPE_MONTH:
        validateDaysOfMonth(testdict[ASCHED])

    ttime = validateTime(testdict[ASCHEDTIME])
    testdict[AHOUR] = ttime.hour
    testdict[AMINUTE] = ttime.minute

    return testdict

class PeriodicTest(object):
    '''
    Class representing a test, data and associated logic
    '''

    def __init__(self, etree=None):

        self.schedule = None
        self.scheduletype = None
        self.scheduletime = None
        self.slot = None
        self.project = None
        self.platform = None
        self.testgroup = None
        self.testrunner = None
        self.testenv = None
        self.os_label = None
        self.dates = None
        self.testhour = None
        self.testminute = None
        self.count = 1

        if etree != None:
            # Initialize from XML if element tree was provided
            # Parsing the XML itself
            testdict = _fromXML(etree)

            # Now setting the attributes
            for k in testdict.keys():
                if k == ACOUNT:
                    self.count = int(testdict[k])
                else:
                    setattr(self, k, testdict[k])

            # Validating the schedule string and splitting the list of dates
            setattr(self, ADATES,
                    set([d.strip().lower()
                         for d in testdict[ASCHED].split(",")]))
            # At this point self.dates is an array of string contains day names
            # or numbers depending on schedule type


    def __str__(self):
        '''
        Convert to string
        '''
        return "/".join([ "%s=%s" % (k, getattr(self, k))
                         for k in TEST_ATTRIBUTES])

    def shortStr(self):
        '''
        Shorter representation for logs
        '''
        testrunner = self.testrunner
        if testrunner == None:
            testrunner = "default"
        return "/".join([ testrunner, self.testgroup,  self.project,  self.slot   ])


    def isForDate(self, date_start, date_end):
        '''
        Check the date specified in the test schedule, with the dates passed
        to the function.
        '''

        daymatches = False

        # First check that the day matches (by name)
        if self.scheduletype == SCHED_TYPE_WEEK:
            daynum = date_start.weekday()
            dayname = DAY_NAMES[daynum]
            # Check that the day name matches
            daymatches = dayname.lower() \
                        in [d.lower()
                            for d in self.dates]# pylint: disable=E1101

        # Otherwise check for the right day of the month
        if self.scheduletype == SCHED_TYPE_MONTH:
            if date_start.day in [int(d) for d in self.dates]:
                daymatches = True

        # Now checking the time itself
        if daymatches:
            test_datetime = date_start.replace(hour=self.testhour,
                                               minute=self.testminute)
            if date_start < test_datetime and  test_datetime < date_end:
                return True
            else:
                return False

    def getBuildMatches(self, buildlist):
        '''
        Return the complete list of test instances matching this test
        (therefore performs the globbing on all slot names etc)
        '''
        matching_tests = []
        for buildinfo in buildlist:
            # First checking the builds matching slots
            __log__.debug(self.testgroup + "Checking against build: %s" % buildinfo["slot"])
            if fnmatch(buildinfo["slot"], self.slot):# pylint: disable=E1101
                # Okay we found a matching slot, now check the projects
                __log__.debug("Slot matches: " + self.slot  )
                for proj in buildinfo["projects"]:
                    if fnmatch(proj["name"].lower(),
                               self.project.lower()): # pylint: disable=E1101
                        # Project matches !
                        __log__.debug("Project matches: " + self.project)
                        for platf in buildinfo["platforms"]:
                            if fnmatch(platf,
                                       self.platform):# pylint: disable=E1101
                                # Platform matches as well, we can add the
                                # triplet to the list
                                sched_test = ScheduledTest(buildinfo["build_id"],
                                                           buildinfo["slot"],
                                                           proj["name"], platf,
                                                           self.testgroup,
                                                           self.testrunner,
                                                           self.os_label,
                                                           self.scheduletype,
                                                           self.scheduletime,
                                                           self.testenv,
                                                           self.count)
                                matching_tests.append(sched_test)
        return matching_tests

class ScheduledTest(object):
    '''
    Class representing a test ready to be run
    '''

    def __init__(self, build_id, slot, project, platform, testgroup,
                 testrunner=None, os_label=None, scheduletype=SCHED_TYPE_WEEK,
                 scheduletime=TIME_DEFAULT, testenv=None, count=1):
        ''' Basic constructor '''
        self.build_id = build_id
        self.slot = slot
        self.project = project
        self.platform = platform
        self.testgroup = testgroup
        self.testrunner = testrunner
        self.os_label = os_label
        self.scheduletype = scheduletype
        self.scheduletime = scheduletime
        self.testenv = testenv
        self.count = count

    def __str__(self):
        '''
        Convert to string
        '''
        return "/".join([ "%s=%s" % (k, getattr(self, k))
                         for k in SCHED_ATTRIBUTES])

    def shortStr(self):
        '''
        Shorter representation for logs
        '''
        return "/".join([ self.testrunner, self.testgroup,  self.project,  self.slot   ])
