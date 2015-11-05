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
artifacts_dir=/data/archive/artifacts

flavours=$(ls ${artifacts_dir} | grep -v lhcb-)
start_dirs=
for f in $flavours ; do
  start_dirs="$start_dirs ${artifacts_dir}/$f"
done

# clean up the artifacts directory (if present)
if [ -e ${artifacts_dir} ] ; then
    echo "$(date): removing old artifacts from ${artifacts_dir}" >> $logfile 2>&1
    find -L ${start_dirs} -depth -mindepth 1 -maxdepth 2 -daystart -mtime +30 -and -path '*/lhcb-*' -print -exec rm -rf \{} \; >> $logfile 2>&1
fi
echo "$(date): done" >> $logfile 2>&1
