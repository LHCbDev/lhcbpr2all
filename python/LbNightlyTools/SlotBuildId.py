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


def get_ids(slots, flavour):
    slot_id_dir = os.path.join(os.environ['JENKINS_HOME'],
                               'nightlies',
                               flavour)
    # slot_id_dir = 'configs'
    slot_id_file = os.path.join(slot_id_dir, 'slot_ids.xml')

    if not os.path.exists(slot_id_dir):
        os.makedirs(slot_id_dir)
        logging.info('Directory %s created', slot_id_dir)

    if os.path.isfile(slot_id_file):
        try:
            xml_parse = ET.parse(slot_id_file)
            root = xml_parse.getroot()

        except:
            logging.error('Can''t find or open %s', slot_id_file)
            sys.exit(1)
    else:
        os.open(slot_id_file, os.O_CREAT, 0644)
        logging.info('File %s created', slot_id_file)
        root = ET.Element('slot_id')
        xml_parse = ET.ElementTree(root)

    res = {}
    add_slot = False

    all_slots = dict((el.get('name'), el) for el in root.findall("slot"))
    for slot_name in slots:
        slot = all_slots.get(slot_name)

        if slot is not None:
            slot_id = slot.get('last_id')
            if not slot_id:
                logging.error('No current_id on the slot %s', slot_name)
                sys.exit(2)
            slot_id = int(slot_id)+1
            slot.set('last_id', str(slot_id))
        else:
            slot_file_build_number = os.path.join(os.environ['JENKINS_HOME'],
                                                  'jobs',
                                                  slot_name,
                                                  'nextBuildNumber')
            if os.path.isfile(slot_file_build_number):
                slot_id = int(open(slot_file_build_number).read())
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

    xml_parse.write(slot_id_file)

    return res

def get_last_ids(slots, flavour):
    slot_id_dir = os.path.join(os.environ['JENKINS_HOME'],
                               'nightlies',
                               flavour)
    # slot_id_dir = 'configs'
    slot_id_file = os.path.join(slot_id_dir, 'slot_ids.xml')

    if os.path.isfile(slot_id_file):
        try:
            xml_parse = ET.parse(slot_id_file)
            root = xml_parse.getroot()

        except:
            logging.error('Can''t find or open %s', slot_id_file)
            sys.exit(1)
    else:
        logging.error('get_last_ids need %s to work', slot_id_file)
        sys.exit(2)

    res = {}

    all_slots = dict((el.get('name'), el) for el in root.findall("slot"))
    for slot_name in slots:
        slot = all_slots.get(slot_name)

        if slot is not None:
            slot_id = slot.get('last_id')
            if not slot_id:
                logging.error('No current_id on the slot %s', slot_name)
                sys.exit(3)
            slot_id = int(slot_id)
        else:
            logging.error('Slot %s have no entrie in %s',
                          slot_name,
                          slot_id_file)
            sys.exit(4)

        res[slot_name] = slot_id

    return res
