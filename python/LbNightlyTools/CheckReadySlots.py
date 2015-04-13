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
Actualy we only avec the slot name in parameter in files

'''
__author__ = 'Colas Pomies <colas.pomies@cern.ch>'

import os
import sys
import glob
import json
from sets import Set
from xml.etree.ElementTree import parse
from LbNightlyTools.Utils import JobParams
from os.path import splitext, basename

def main(*argv):
    '''
    Main script function.
    '''
    if not argv:
        prog = os.path.basename(sys.argv[0])
        argv = sys.argv[1:]
    else:
        prog = __name__

    usage = ('Usage: {0} output_file_format\n'
             'Example:\n'
             '\t{0} "slot-param-{{}}.txt"').format(prog)

    if '-h' in argv or '--help' in argv:
        print usage
        sys.exit(0)

    if len(argv) != 1:
        print >>sys.stderr, usage
        sys.exit(1)

    output_file = argv[0]

    slots = Set()

    #get all json files for slot configuration
    files = glob.glob('configs/lhcb-*.json')


    for file_name in files:
        with open(file_name) as data_file:
            data = json.load(data_file)
            #check if slot is not disable
            if (not 'disabled' in data) or data['disabled'] == False:
                #extract attribute slot if exist
                if u'slot' in data:
                    slots.add(data['slot'])
                # if not extract slot name from filename
                else:
                    slots.add(splitext(basename(file_name))[0])



    xmlParse = parse('configs/configuration.xml')
    #Extract all slots name from configuration who doesn't have attribute disabled to true
    slots = slots | Set(el.get('name') for el in xmlParse.findall("slot") if el not in xmlParse.findall("slot[@disabled='true']"))
    print '\n'.join(slots)

    ready = []

    #Init parameters for each slot
    for slot in slots:
        ready.append(JobParams(slot=slot))

    #Create a file that contain JobParams for each slot
    for i, test_params in enumerate(ready):
            open(output_file.format(i), 'w').write(str(test_params) + '\n')
            print output_file.format(i), 'written.'

