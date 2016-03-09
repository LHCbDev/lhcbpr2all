###############################################################################
# (c) Copyright 2016 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
'''
Module grouping the common build functions.
'''
__author__ = 'Ben Couturier <ben.couturier@cern.ch>'

import LbNightlyTools

import datetime
import os
import pika #Requires previous import of LbNightlyTools
import json
from Common import Messenger

class TestMessenger(Messenger):
    '''
    Class used to connect to the queue of periodic tests to be run
    '''
    def __init__(self):
        '''
        Initialize props
        '''
        Messenger.__init__(self)
        self._topic_name = "topic.periodic_test"


    def requestTest(self, slot, buildId, project, config, group, env,
                    runner, os_label):
        '''
        Sends the request fot starting a test
        '''
        params = [ slot, project, config, group, env ]
        routingKey = ".".join(params)
        body = json.dumps([ slot, buildId, project, config,
                            group, env, runner, os_label ])
        self._basicPublish(routingKey, body)


    def getTestToRun(self, queueName=None, bindingKeys=None):
        '''
        List the waiting requests for tests to be run
        '''
        test_list = []
        with self._getConnection() as connection:
            (channel, queueName) = self._setupClientChannel(connection.channel(),
                                                            queueName, bindingKeys)
            while True:
                method_frame, header_frame, body = channel.basic_get(queue=queueName)
                if method_frame == None:
                    break
                t = json.loads(body)
                test_list.append(t)
                channel.basic_ack(method_frame.delivery_tag)
        return test_list

    def processTestToRun(self, callback, queueName=None, bindingKeys=None, ):
        '''
        List the waiting requests for tests to be run
        '''
        test_list = []
        with self._getConnection() as connection:
            (channel, queueName) = self._setupClientChannel(connection.channel(),
                                                            queueName, bindingKeys)
            idx = 0
            while True:
                method_frame, header_frame, body = channel.basic_get(queue=queueName)
                if method_frame == None:
                    break
                t = json.loads(body)
                callback(idx, t)
                idx += 1
                channel.basic_ack(method_frame.delivery_tag)
