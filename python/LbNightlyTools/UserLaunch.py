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
Simple script to manage the request from on user job
'''
__author__ = 'Colas Pomies <colas.pomies@cern.ch>'

from LbNightlyTools.Utils import JobParams
from LbNightlyTools.SlotBuildId import get_ids, get_last_ids
import LbUtils.Script


class Script(LbUtils.Script.PlainScript):
    '''
    Script to create one file for all enable slots or for slots in parameters
    This file contain the slot name and the slot build id
    The slot build id is extract with the function get_ids
    '''
    __usage__ = '%prog [options] flavour output_checkout.txt slots'
    __version__ = ''

    def defineOpts(self):

        self.parser.add_option('--slot-build-id',
                               action='store',
                               help='define the slot_build_id to use')

        self.parser.add_option('--rebuild-last-id',
                               action='store_true',
                               dest='rebuild_last_id',
                               help='build with the last slot_build_id')

        self.parser.add_option('--no-checkout',
                               action='store_true',
                               dest='no_checkout',
                               help='build without checkout slot')

        self.parser.set_defaults(slot_build_id="",
                                 rebuild_last_id=False,
                                 no_checkout=False)

    def write_files(self, slots, flavour, output_file, rebuild_last_id, no_checkout, slot_build_id_def):
        if slot_build_id_def == "":
            if rebuild_last_id:
                slot_ids = get_last_ids(slots, flavour)
            else:
                slot_ids = get_ids(slots, flavour)


        for slot in slots:
            output_file_name = output_file.format(slot)
            if slot_build_id_def == "":
                slot_build_id=slot_ids[slot]
            else:
                slot_build_id=slot_build_id_def

            open(output_file_name, 'w') \
                .write(str(JobParams(slot=slot,
                                     slot_build_id=slot_build_id,
                                     no_checkout=no_checkout
                                     )) + '\n')

            self.log.info('%s written for slot %s with build id %s',
                          output_file_name,
                          slot,
                          slot_build_id)

        self.log.info('%s slots to start', len(slots))

    def main(self):
        if len(self.args) != 3:
            self.parser.error('wrong number of arguments')

        opts = self.options

        flavour = self.args[0]
        output_file = self.args[1]
        slots = self.args[2].strip().split(' ')

        if len(slots) > 1 and opts.slot_build_id != "":
            self.log.error('Can''t define slot_build_id with multiple slots')
            return 1

        # Create a file that contain JobParams for each slot
        self.write_files(slots, flavour, output_file, opts.rebuild_last, opts.slot_build_id)

        self.log.info('End of manage user launch')

        return 0
