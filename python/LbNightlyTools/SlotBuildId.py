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
Script to get and set current slot_build_id of a slot

'''
__author__ = 'Colas Pomies <colas.pomies@cern.ch>'

import sys
from xml.etree.ElementTree import parse, Element

import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
        TODO : Explain the script
    '''
    __usage__ = '%prog [options] <slot1> <slot2> <slot3> ...'
    __version__ = ''
    def main(self):

        if len(self.args) < 1:
            self.parser.error('wrong number of arguments')

        slot_id_file = 'configs/slot_id.xml'

        try:
            xmlParse = parse(slot_id_file)

        except:
            self.log.error('Can''t find or open %s', slot_id_file)
            sys.exit(1)

        res = {}
        root = xmlParse.getroot()

        for slot_name in self.args:
            slots = root.findall("slot[@name='"+slot_name+"']")

            if len(slots):
                slot = slots[0]
                slot_id = slot.get('current_id')
                if not slot_id:
                    self.log.error('no attribute current_id on the slot %s', slot_name)
                    sys.exit(2)
                slot_id = int(slot_id)+1
                slot.set('current_id', str(slot_id))
            else:
                slot_id = 1
                slot = Element('slot')
                slot.set('name', slot_name)
                slot.set('current_id', str(slot_id))
                root.append(slot)
                self.log.info('Creation du slot %s dans slot_id.xml', slot_name)

            res[slot_name] = slot_id

        xmlParse.write(slot_id_file)


        return res