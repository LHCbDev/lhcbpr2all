#!/usr/bin/env python
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
Simple script to extract the list of requested platforms from the slot
configuration file.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import sys

def parseConfigFile(path):
    from LbNightlyTools.Configuration import load
    data = load(path)
    return data.get(u'default_platforms', [])

if __name__ == '__main__':
    usage = 'Usage: %s configuration_file' % os.path.basename(sys.argv[0])

    if '-h' in sys.argv or '--help' in sys.argv:
        print usage
        sys.exit(0)

    if len(sys.argv) != 2:
        print >>sys.stderr, usage
        sys.exit(1)

    print ' '.join(parseConfigFile(sys.argv[1]))
