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

class NightliesMessenger(Messenger):
    '''
    Class used to connect to the NightlyBuilds queue
    '''
    def __init__(self):
        '''
        Initialize props
        '''
        Messenger.__init__(self)
        self._topic_name = "topic.build_ready"

    
    def sendBuildDone(self, slot, project, config, buildId, date=datetime.datetime.now()):
        '''
        Sends the message that a particular project has been built
        '''
        self._basicPublish(".".join([slot, project, config]),
                           json.dumps([slot, project, config, buildId]))


    def getBuildsDone(self, queueName=None, bindingKeys=None):
        '''
        Get the list of builds done, for whcih messages are queued
        '''
        def callback(ch, method, properties, body):
            print("%r\t%r" % (method.routing_key, body))

        with self._getConnection() as connection:
            (channel, queueName) = self._setupClientChannel(connection.channel(),
                                                            queueName, bindingKeys)
            while True:
                method_frame, header_frame, body = channel.basic_get(queue=queueName)
                if method_frame == None:
                    break
                print method_frame.routing_key, body
                channel.basic_ack(method_frame.delivery_tag)
             

    def consumeBuildsDone(self, callback, queueName=None, bindingKeys=None):
        '''
        Get the list of builds done, for which messages are queued
        It takes a callback like so:
        def callback(ch, method, properties, body):
            print(" [x] %r:%r" % (method.routing_key, body))
        '''

        with self._getConnection() as connection:
            (channel, queueName) = self._setupClientChannel(connection.channel(),
                                                            queueName, bindingKeys)
            channel.basic_consume(callback,
                                  queue=queueName,
                                  no_ack=True)
            channel.start_consuming()
