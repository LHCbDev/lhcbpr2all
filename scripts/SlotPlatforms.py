#!/usr/bin/env python
'''
Simple script to extract the list of requested platforms from the slot
configuration file.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import sys

def parseConfigFile(path):
    from LHCbNightlies2.Configuration import load
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
