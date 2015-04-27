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
from platform import platform
'''
Module containing the classes and functions used to check if a slot have
preconditions and write files with parameters for next jobs in Jenkins
'''
__author__ = 'Colas Pomies <colas.pomies@cern.ch>'

import os

from LbNightlyTools.Configuration import load
from LbNightlyTools.Utils import JobParams

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

        data = load(self.args[0])
        preconds = data.get(u'preconditions', [])
        if preconds:
            output_file = 'slot-precondition-{0}-{1}.txt'
        else:
            output_file = 'slot-build-{0}-{1}.txt'

        if os.environ.has_key('platforms') and os.environ['platforms'] != '':
            platforms = os.environ['platforms'].split()
        else:
            platforms = data.get(u'default_platforms', [])


        for platform in platforms:
            os_label = platform.split('-')[1]
            output_file_name = output_file.format(os.environ['slot'], platform)
            open(output_file_name, 'w') \
                .write(str(JobParams(slot=os.environ['slot'],
                                     slot_build_id=os.environ['slot_build_id'],
                                     platform=platform,
                                     os_label=os_label,
                                     preconditions=preconds
                                     )) + '\n')
            self.log.debug('%s written', output_file_name)

        return 0
