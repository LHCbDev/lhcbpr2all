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
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import sys
import time
import json
import codecs

from stat import ST_CTIME

DATA_DIR = '/data/archive'

from LbNightlyTools.Utils import JobParams

def main(*argv):
    '''
    Main script function.
    '''
    if not argv:
        prog = os.path.basename(sys.argv[0])
        argv = sys.argv[1:]
    else:
        prog = __name__

    usage = ('Usage: {0} working_directory output_file_format\n'
             'Example:\n'
             '\t{0} /path/to/a/dir "test-{{}}.txt"').format(prog)

    if '-h' in argv or '--help' in argv:
        print usage
        sys.exit(0)

    if len(argv) != 2:
        print >>sys.stderr, usage
        sys.exit(1)

    work_dir, output_file = argv
    global_file = work_dir + '.json'
    data_dir = os.environ.get('DATA_DIR', DATA_DIR)

    try:
        with codecs.open(global_file, 'r', 'utf-8') as f:
            expected_builds = json.load(f)
    except:
        expected_builds = []

    # timestamp before which we can assume the build will never appear
    expired_timestamp = time.time() - (18 * 60 * 60) # 18 hours ago

    from os.path import join

    for root, _dirs, files in os.walk(work_dir):
        for f in files:
            f = join(root, f)
            try:
                expected_builds.extend(json.load(codecs.open(f, 'r', 'utf-8')))
                os.remove(f)
            except Exception, x:
                print "Ignoring '%s': %s" % (f, x)

    # check for binary tarballs
    pending = []
    ready = []
    for expected in expected_builds:
        (filename, slot, build_id, project, platform, timestamp,
         os_label) = expected
        if timestamp < expired_timestamp:
            print slot, build_id, project, platform, 'dropped'
            continue # request too old, skip
        # check that the trigger file file exists and it is not older than the
        # request
        path = os.path.join(data_dir, filename)
        if (len(ready) < 20 and
            os.path.exists(path) and
            os.stat(path)[ST_CTIME] >= timestamp):
            ready.append(JobParams(slot=slot,
                                   slot_build_id=build_id,
                                   project=project,
                                   platform=platform,
                                   os_label=os_label))
            print slot, build_id, project, platform, 'ready'
        else:
            pending.append(expected)

    if ready:
        for i, test_params in enumerate(ready):
            open(output_file.format(i), 'w').write(str(test_params) + '\n')
            print output_file.format(i), 'written.'
            print test_params
        print len(ready), 'test jobs to start.'

    # store the still pending builds
    global_dir = os.path.dirname(global_file)
    if global_dir and not os.path.exists(global_dir):
        os.makedirs(global_dir)
    with codecs.open(global_file, 'w', 'utf-8') as f:
        json.dump(pending, f, indent=2)