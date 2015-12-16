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
Created on Jan 15, 2014

Interface to the LHCbPR System.

@author: Ben Couturier
'''
import urllib2
import json

HEADERS = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

class JobManager(object):
    '''
    Interface to the LHCbPR system
    '''
    def __init__(self, lhcbpr_host=None, lhcbpr_url=None):
        '''
        Constructor taking the URL for the LHCbPR server
        '''
        if lhcbpr_host == None:
            lhcbpr_host = "lblhcbpr2.cern.ch"
        if lhcbpr_url == None:
            lhcbpr_url = "api"

        self._lhcbpr_host = lhcbpr_host
        self._lhcbpr_url = lhcbpr_url

    def getJobOptions(self, options_description):
        ''' Get the list of options from LHCbPR2 '''

        resp = urllib2.urlopen('http://%s/%s/options/?description=%s' % (self._lhcbpr_host,
                                                                         self._lhcbpr_url,
                                                                         options_description)).read()
        data = json.loads(resp)
        if data["count"] == 0:
            return None
        prdata = data["results"][0]
        return prdata["content"]



    def getSetupOptions(self, setup_description):
        ''' Get the SetupProject options from LHCbPR2 '''

        resp = urllib2.urlopen('http://%s/%s/setups/?description=%s' % (self._lhcbpr_host,
                                                                         self._lhcbpr_url,
                                                                         setup_description)).read()
        data = json.loads(resp)
        if data["count"] == 0:
                return None
        prdata = data["results"][0]
        return prdata["content"]



