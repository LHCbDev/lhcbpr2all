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

from LbNightlyTools.Scripts.Common import findSlot
from LbNightlyTools.Utils import JobParams

import os

import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Script to check if a slot have preconditions or can be built right away.
    '''
    __usage__ = '%prog [options] <slot> <slot_build_id> <flavour>'
    __version__ = ''

    def defineOpts(self):

        self.parser.add_option('--platforms',
                               action='store',
                               help='Platforms to build the slot')

        self.parser.set_defaults(platforms="")

    def main(self):
        '''
        Script main function.
        '''
        if len(self.args) != 3:
            self.parser.error('wrong number of arguments')

        opts = self.options

        # FIXME: to be ported to the new configuration classes
        slot, slot_build_id, flavour = self.args
        slot = findSlot(slot)

        preconds = slot.preconditions
        if preconds:
            self.log.info('Found preconditions for %s', slot.name)
            output_file = 'slot-precondition-{0}-{1}.txt'
        else:
            self.log.info('No preconditions for %s', slot.name)
            output_file = 'slot-build-{0}-{1}.txt'

        platforms = opts.platforms.strip().split() or slot.platforms

        if flavour == 'release':
            label = '-release'
        elif os.environ.get('os_label') == 'coverity':
            label = '-coverity'
        else:
            label = '-build'

        for platform in platforms:
            os_label = platform.split('-')[1] + label
            output_file_name = output_file.format(slot.name, platform)
            open(output_file_name, 'w') \
                .write(str(JobParams(slot=slot.name,
                                     slot_build_id=slot_build_id,
                                     platform=platform,
                                     os_label=os_label,
                                     )) + '\n')
            self.log.debug('%s written', output_file_name)

        return 0
