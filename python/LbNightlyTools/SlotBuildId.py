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

import logging
import os
import sys
import xml.etree.ElementTree as ET

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def getIds(slots):
    #slot_id_dir = os.environ['JENKINS_HOME']+'/nightlies/'+os.environ['flavours']
    slot_id_dir = 'configs/'
    slot_id_file = os.path.join(slot_id_dir, 'slot_id.xml')

    if not os.path.exists(slot_id_dir):
        os.makedirs(slot_id_dir)

    if os.path.isfile(slot_id_file):
        try:
            xmlParse = ET.parse(slot_id_file)
            root = xmlParse.getroot()

        except:
            logging.error('Can''t find or open %s', slot_id_file)
            sys.exit(1)
    else:
        os.open(slot_id_file, os.O_CREAT, 0644)
        root = ET.Element('slot_id')
        xmlParse = ET.ElementTree(root)

    res = {}
    add_slot = False

    all_slots = dict((el.get('name'), el) for el in root.findall("slot"))
    for slot_name in slots:
        slot = all_slots.get(slot_name)

        if slot is not None:
            slot_id = slot.get('last_id')
            if not slot_id:
                logging.error('No attribute current_id on the slot %s', slot_name)
                sys.exit(2)
            slot_id = int(slot_id)+1
            slot.set('last_id', str(slot_id))
        else:
            slot_id = 1
            slot = ET.Element('slot')
            slot.set('name', slot_name)
            slot.set('last_id', str(slot_id))
            root.append(slot)
            add_slot = True
            logging.info('Slot %s created in %s', slot_name, slot_id_file)

        res[slot_name] = slot_id

    if add_slot:
        indent(root)

    xmlParse.write(slot_id_file)

    return res
