#!/usr/bin/env python
'''
Module containing the classes and functions used to verify preconditions for
building a slot.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import logging

from datetime import datetime, timedelta
from time import sleep
from os.path import exists

def waitForFile(path, timeout=timedelta(hours=12), maxAge=None):
    '''
    Wait until a file becomes available, but not more than the timedelta specified
    as timeout.
    If maxAge is not None, it must be a timedelta and an existing file is ignored if
    it is older than that age.

    @return: True if a valid file appeared within the timeout, False otherwise
    '''
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)

    logging.debug('waiting for file %s', path)

    def fileTime(path):
        '''helper to return the datetime of last modification of a file'''
        return datetime.fromtimestamp(os.path.getmtime(path))

    now = datetime.now()

    whenToStop = now + timeout

    if maxAge:
        minFileDate = now - maxAge
    else:
        minFileDate = datetime.fromtimestamp(0)

    while datetime.now() < whenToStop:
        if exists(path) and fileTime(path) > minFileDate:
            return True
        sleep(60)

    return False


def parseConfigFile(path):
    from Configuration import load
    data = load(path)
    return data.get(u'preconditions', [])


import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Script to Check.

    The configuration file must be in JSON format containing an object with the
    attribute 'projects', a list of objects with defining the projects to be
    checked out.

    For example::
        {"preconditions": [{"name": "waitForFile",
                            "args": {"path": "path/to/file"}}]}
    '''
    __usage__ = '%prog [options] <config.json>'
    __version__ = ''

    def main(self):
        '''
        Script main function.
        '''
        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        preconds = parseConfigFile(self.args[0])

        from _utils import setDayNamesEnv
        setDayNamesEnv()

        starttime = datetime.now()
        for precond in preconds:
            name = precond[u'name']
            args = precond.get(u'args', {})
            f = globals()[name]
            self.log.info('running %s(%s)', name, args)
            if f(**args):
                self.log.debug('precondition met')
            else:
                self.log.error('precondition failed')
                return 1

        self.log.info('all preconditions are met (time taken: %s).', datetime.now() - starttime)
        return 0
