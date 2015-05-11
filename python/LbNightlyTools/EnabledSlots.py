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
Simple script to extract slot who need to be compile
Create one file for each slot. Each file contains parameters for the next job.
Now we only have the slot name in parameter in files
'''
__author__ = 'Colas Pomies <colas.pomies@cern.ch>'

import os
import glob
import json
from xml.etree.ElementTree import parse
from LbNightlyTools.Utils import JobParams
from os.path import splitext, basename
from LbNightlyTools.SlotBuildId import get_ids
import LbUtils.Script


class Script(LbUtils.Script.PlainScript):
    '''
    Script to create one file for all enable slots or for slots in parameters
    This file contain the slot name and the slot build id
    The slot build id is extract with the function get_ids
    '''
    __usage__ = '%prog [options] flavour <output_file.txt> [<slot1> <slot2> ...]'
    __version__ = ''

    def defineOpts(self):
        self.parser.add_option('--config-dir',
                               action='store',
                               help='Directoryto find configurations files')

        self.parser.add_option('--slots',
                               action='store',
                               help='Slots to activate')

        self.parser.set_defaults(config_dir=".",
                                 slots=None)

    def extract_from_json(self, file_format_json):
        self.log.info('Extract slots from %s files', file_format_json)

        slots = set()

        # get all json files for slot configuration
        files = glob.glob(file_format_json)

        for file_name in files:
            try:
                with open(file_name) as data_file:
                    data = json.load(data_file)
                    # check if slot is not disable
                    if ('disabled' not in data) or data['disabled'] is False:
                            # extract attribute slot if exist
                        if 'slot' in data:
                            slot_name = data['slot']
                        # if not extract slot name from filename
                        else:
                            slot_name = splitext(basename(file_name))[0]
                        slots.add(slot_name)
                        self.log.debug('Add %s to the slot list from %s',
                                       slot_name, file_name)
            except:
                self.log.warning('Can''t find or open %s', file_name)

        self.log.info('%s slots from %s', len(slots), file_format_json)

        return slots

    def extract_from_xml(self, config_file):
        self.log.info('Extract slots from %s', config_file)

        try:
            xml_parse = parse(config_file)

        except:
            self.log.warning('Can''t find or open %s', config_file)
            return set()

        # Extract all slots name from xml configuration file
        # Extract slots with no attribute disabled or set to False
        self.log.debug('Get slot from %s', config_file)
        slots = set(el.get('name')
                    for el in xml_parse.findall("slot")
                    if el.attrib.get('disabled', 'false').lower() != 'true')
        self.log.info('%s slots from %s', len(slots), config_file)

        return slots

    def write_files(self, slots, flavour, output_file):
        slot_ids = get_ids(slots, flavour)
        for slot in slots:
            output_file_name = output_file.format(slot)
            slot_build_id=slot_ids[slot]
            open(output_file_name, 'w') \
                .write(str(JobParams(slot=slot,
                                     slot_build_id=slot_build_id
                                     )) + '\n')
            self.log.info('%s written for slot %s with build id %s',
                          output_file_name,
                          slot,
                          slot_build_id)

        self.log.info('%s slots to start', len(slots))

    def main(self):
        if len(self.args) != 2:
            self.parser.error('wrong number of arguments')

        opts = self.options

        flavour = self.args[0]
        output_file = self.args[1]

        if not opts.slots:
            self.log.info('Starting extraction of all enable slot')
            slots = self.extract_from_json(os.path.join(opts.config_dir,'lhcb-*.json')) | \
                self.extract_from_xml(os.path.join(opts.config_dir,'configuration.xml'))
        else:
            slots=opts.slots.strip().split(' ');

        # Create a file that contain JobParams for each slot
        self.write_files(slots, flavour, output_file)

        self.log.info('End of extraction of all enable slot')

        return 0
