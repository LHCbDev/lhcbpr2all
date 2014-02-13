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
import logging
from xml.etree.ElementTree import ElementTree
from LbPeriodicTools.LbPeriodicTest import PeriodicTest

__log__ = logging.getLogger(__name__)

class PeriodicTestSchedule(object):
    '''
    Parser to the periodic test scheduling XML file
    '''
    def __init__(self, filename, rethrow_exceptions=False):
        '''
        Constructor that takes the schedule filename as parameter
        '''
        self._filename = filename
        self._tests = []
        self._tree = None
        self._parse(rethrow_exceptions)

    def _parse(self, rethrow=False):
        '''
        Parse the file specified and save the ElementTree
        '''
        tree = ElementTree()
        tree.parse(self._filename)

        for child in tree.getroot():
            try:
                ptest = PeriodicTest(child)
                self._tests.append(ptest)
            except ValueError, val:
                __log__.error(val)
                if rethrow:
                    raise val

    def getTests(self, predicate=None):
        '''
        Parse the file specified and save the ElementTree
        '''
        if predicate == None:
            return self._tests
        else:
            return [ t for t in self._tests if predicate(t)]

