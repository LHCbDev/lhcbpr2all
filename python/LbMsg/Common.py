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

class Messenger(object):
    '''
    Class used to send messages to the build system message broker
    '''
    def __init__(self, host=None,
                 user=None, passwd=None,
                 port=5671, vhost='/lhcb'):
        '''
        Initialize the messenging class
        '''
        # Setup the credential variables        
        if host == None:
            host = "lhcb-jenkins.cern.ch"
        self._host = host
        if user == None or passwd == None:
            (username, passwd) = self._getPwdFromSys()
            if user == None:
                user = username
        self._credentials =  pika.PlainCredentials(user, passwd)

        # And the connection params
        self._port = port
        self._vhost = vhost
        

    def _getConnection(self):
        '''
        Creates connection to rabbitMQ ond emand
        '''
        params = pika.ConnectionParameters(self._host,
                                           ssl=True,
                                           port=self._port,
                                           virtual_host=self._vhost,
                                           credentials=self._credentials)
        return pika.BlockingConnection(params)
        
    def _getPwdFromSys(self):
        '''
        Get the RabbitMQ password from the environment of from a file on disk
        '''
        # First checing the environment
        res = os.environ.get("RMQPWD", None)

        # Checking for the password in $HOME/private/rabbitmq.txt
        if res == None:
            fname = os.path.join(os.environ["HOME"], "private", "rabbitmq.txt")
            if os.path.exists(fname):
                with open(fname, "r") as f:
                    data = f.readlines()
                    if len(data) > 0:
                        res = data[0].strip()

        # Separate the username/password
        (username, password) = res.split("/")
        return (username, password)

    def _setupChannel(self, channel):
            channel.exchange_declare(exchange=self._topic_name,
                                     durable=True,
                                     type='topic')
            return channel
            
    def _basicPublish(self, routingKey, body):
        '''
        Send a message to the topic defined for the builds
        '''
        with self._getConnection() as connection:
            channel = self._setupChannel(connection.channel())
            props = pika.BasicProperties(delivery_mode = 2) # make message persistent
            channel.basic_publish(exchange=self._topic_name,
                                  routing_key=routingKey,
                                  body=body,
                                  properties=props)
    
        
    def _setupClientChannel(self, channel, queueName=None, bindingKeys=None):
        '''
        Setup the chlient channel to receive the approriate messages
        '''
        channel = self._setupChannel(channel)
        if queueName == None:
            # Anonymous queue is NOT persistent
            result = channel.queue_declare(exclusive=True)
            queueName = result.method.queue
        else:
            # Named queues are persistent...
            result = channel.queue_declare(durable=1, queue=queueName)

        if bindingKeys == None:
            bindingKeys = [ "#" ]

        # Now binding the queue to the topic
        for bindingKey in bindingKeys:
            channel.queue_bind(exchange=self._topic_name,
                               queue=queueName,
                               routing_key=bindingKey)

        return (channel, queueName)


