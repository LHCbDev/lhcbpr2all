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

# Remove old data from the artifacts archive directory.

# prepare environment

# hard-coded because it may point to CVMFS
export LHCBNIGHTLIES=/afs/cern.ch/lhcb/software/nightlies

logfile=$LHCBNIGHTLIES/www/logs/cleanup_artifacts.log
artifacts_dir=/data/artifacts

# clean up the artifacts directory (if present)
if [ -e ${artifacts_dir} ] ; then
    echo "$(date): removing old artifacts from ${artifacts_dir}" >> $logfile 2>&1
    find -L ${artifacts_dir}/testing ${artifacts_dir} -depth -mindepth 1 -maxdepth 2 -daystart -mtime +15 -and -not -name testing -print -exec rm -rf \{} \; >> $logfile 2>&1
fi
echo "$(date): done" >> $logfile 2>&1
