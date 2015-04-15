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

import glob
import json
from sets import Set
from xml.etree.ElementTree import parse
from LbNightlyTools.Utils import JobParams
from os.path import splitext, basename

import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
        TODO : Explain the script
    '''
    __usage__ = '%prog [options] <format_output_file.txt>'
    __version__ = ''

    def extractFromJson(self, file_format_json):
        self.log.info('Extract slots from %s files', file_format_json)

        slots = Set()

        #get all json files for slot configuration
        files = glob.glob(file_format_json)


        for file_name in files:
            try:
                with open(file_name) as data_file:
                    data = json.load(data_file)
                    #check if slot is not disable
                    if (not 'disabled' in data) or data['disabled'] == False:
                            #extract attribute slot if exist
                        if 'slot' in data:
                            slot_name = data['slot']
                        # if not extract slot name from filename
                        else:
                            slot_name = splitext(basename(file_name))[0]
                        slots.add(slot_name)
                        self.log.debug('Add %s to the slot list from %s', slot_name, file_name)
            except:
                self.log.warning('Can''t find or open %s', file_name)


        self.log.info('%s slots from %s', len(slots), file_format_json)

        return slots

    def extractFromXml(self, config_file):
        self.log.info('Extract slots from %s', config_file)

        slots = Set()

        try:
            xmlParse = parse(config_file)
            #Extract all slots name from configuration who doesn't have attribute disabled to true
            self.log.debug('Get slot from %s', config_file)
            slots = Set(el.get('name') for el in xmlParse.findall("slot") if el not in xmlParse.findall("slot[@disabled='true']"))
            self.log.info('%s slots from %s', len(slots), config_file)

        except:
            self.log.warning('Can''t find or open %s', config_file)

        return slots

    def writeFiles(self, slots, output_file):
        for slot in slots:
            output_file_name = output_file.format(slot)
            open(output_file_name, 'w').write(str(JobParams(slot=slot)) + '\n')
            self.log.debug('%s written', output_file_name)

        self.log.info('%s slots to start', len(slots))


    def main(self):

        self.log.info('Starting extraction of all enable slot')

        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        output_file = self.args[0]

        slots = self.extractFromJson('configs/lhcb-*.json') | self.extractFromXml('configs/configuration.xml')

        #Create a file that contain JobParams for each slot
        self.writeFiles(slots, output_file)

        self.log.info('End of extraction of all enable slot')

        return 0