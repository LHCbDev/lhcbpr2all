#!/bin/bash
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

echo Waiting for ${project} ${platform}...

# 5 minutes between each check
poll_interval=300
# number of checks to wait for 12 hours
countdown=$(( 12 * 60 * 60 / ${poll_interval} ))

while [ ${countdown} -ge 0 ] ; do
    sleep 300
    filename=/data/${ARTIFACTS_DIR}/${project}.*.${slot_build_id}.*.${platform}.tar.bz2
    if [ -e ${filename} ] ; then
        break
    fi
    countdown=$(( ${countdown} - 1 ))
done

if [ ! -e ${filename} ] ; then
    echo "ERROR: the binary tarball did not appear in 12 hours"
    exit 1
fi
