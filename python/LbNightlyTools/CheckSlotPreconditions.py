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

from LbNightlyTools.ScriptsCommon import findSlot
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
    __usage__ = '%prog [options] <config.json> <slot> <slot_build_id>'
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
        if len(self.args) != 4:
            self.parser.error('wrong number of arguments')

        opts = self.options

        # FIXME: to be ported to the new configuration classes
        data = findSlot(self.args[0]).toDict()
        slot = self.args[1]
        slot_build_id = self.args[2]
        flavour = self.args[3]

        preconds = data.get(u'preconditions', [])
        if preconds:
            self.log.info('Find precondition for %s', slot)
            output_file = 'slot-precondition-{0}-{1}.txt'
        else:
            self.log.info('No precondition for %s', slot)
            output_file = 'slot-build-{0}-{1}.txt'

        platforms = opts.platforms.strip().split()

        if not platforms:
            platforms = data.get(u'default_platforms', [])


        label = '-build'
        if (flavour == 'release'):
            label = '-release'

        for platform in platforms:
            os_label = platform.split('-')[1]+label
            output_file_name = output_file.format(slot, platform)
            open(output_file_name, 'w') \
                .write(str(JobParams(slot=slot,
                                     slot_build_id=slot_build_id,
                                     platform=platform,
                                     os_label=os_label,
                                     )) + '\n')
            self.log.debug('%s written', output_file_name)

        return 0
