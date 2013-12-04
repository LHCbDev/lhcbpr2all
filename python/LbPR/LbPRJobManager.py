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
import httplib
import urllib
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
            lhcbpr_host = "lhcb-pr.web.cern.ch"
        if lhcbpr_url == None:
            lhcbpr_url = "/lhcb-pr/"

        self._lhcbpr_host = lhcbpr_host
        self._lhcbpr_url = lhcbpr_url

    def getOrCreateJobDescription(self, application, version,
                                  options, setup_options):
        '''
        Returns the Job description ID for the requested parameters

        Here is the equivalent wget command:
        wget -q -O-  --post-data="application=${app}&version=${ver}&options=${optio}&optionsD=${optD}&setupprojectD=${setD}"\
        http://lhcb-pr.web.cern.ch/lhcb-pr/newjobdescription

        '''
        params = urllib.urlencode({
            'application' : application.upper(),
            'version' : version,
            'optionsD' : options,
            'setupprojectD' : setup_options
            })

        headers = HEADERS

        conn = httplib.HTTPConnection(self._lhcbpr_host)
        conn.request("POST", self._lhcbpr_url + "newjobdescription",
                     params, headers)
        response = conn.getresponse()
        if response.status != httplib.OK:
            raise Exception("Connection error with %s: %s %s"
                            % (self._lhcbpr_host, response.status,
                               response.reason))
        datastr = response.read()
        conn.close()
        data = json.loads(datastr)
        if data['error']:
            raise Exception(data['errorMessage'])
        return data["jobdescription_id"]


    def getJobOptions(self, options_description):
        ''' Get the list of options from LHCbPR '''
        params = urllib.urlencode({
            'optionsD' : options_description
            })

        headers = HEADERS

        conn = httplib.HTTPConnection(self._lhcbpr_host)
        conn.request("POST", self._lhcbpr_url + "getcontent",
                     params, headers)
        response = conn.getresponse()
        if response.status != httplib.OK:
            raise Exception("Connection error with %s: %s %s"
                            % (self._lhcbpr_host, response.status,
                               response.reason))
        datastr = response.read()
        conn.close()
        data = json.loads(datastr)
        if data['error']:
            raise Exception(options_description + ":" + data['errorMessage'])
        return data["content"]

    def getSetupOptions(self, setup_description):
        ''' Get the SetupProject options from LHCbPR '''
        params = urllib.urlencode({
             'setupprojectD' : setup_description
            })

        headers = HEADERS

        conn = httplib.HTTPConnection(self._lhcbpr_host)
        conn.request("POST", self._lhcbpr_url + "getcontent", params, headers)
        response = conn.getresponse()
        if response.status != httplib.OK:
            raise Exception("Connection error with %s: %s %s"
                            % (self._lhcbpr_host, response.status,
                               response.reason))
        datastr = response.read()
        conn.close()
        data = json.loads(datastr)
        if data['error']:
            raise Exception(setup_description + ":" + data['errorMessage'])
        return data["content"]

