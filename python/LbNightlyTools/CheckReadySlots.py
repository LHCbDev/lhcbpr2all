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
Simple script to poll for expected builds and report which of them are ready
to be tested.

Given an "inbox" directory, retrieve the list of new expected builds, update the
global list and check which builds are ready, then create a parameter file for
each build that is ready to be tested, with the parameters
- slot
- slot_build_id
- project
- platform
- os_label

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

    files = glob.glob('configs/lhcb-*.json')


    for file_name in files:
        with open(file_name) as data_file:
            data = json.load(data_file)
            if (not 'disabled' in data) or data['disabled'] == False:
                if u'slot' in data:
                    slots.add(data['slot'])
                else:
                    slots.add(splitext(basename(file_name))[0])



    xmlParse = parse('configs/configuration.xml')
    slots = slots | Set(el.get('name') for el in xmlParse.findall("slot") if el not in xmlParse.findall("slot[@disabled='true']"))
    print '\n'.join(slots)

    ready = []

    for slot in slots:
        ready.append(JobParams(slot=slot))


    for i, test_params in enumerate(ready):
            open(output_file.format(i), 'w').write(str(test_params) + '\n')
            print output_file.format(i), 'written.'

