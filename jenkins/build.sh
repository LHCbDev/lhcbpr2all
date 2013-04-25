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

export ARTIFACTS_DIR=${ARTIFACTS_DIR:-artifacts/${slot}/${slot_build_id}}
export TMPDIR=$WORKSPACE/tmp
mkdir -p $TMPDIR

echo ===================================================================
echo Worker Node: $NODE_NAME
echo Workspace: $WORKSPACE
echo Artifacts dir: $ARTIFACTS_DIR
echo ===================================================================

# Clean LD_LIBRARY_PATH of /gcc/ entries (see comment on issue LBCORE-109 http://cern.ch/go/PLQ7)
export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH | tr : \\n | grep -v /gcc/ | tr \\n :)

. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh -c $platform

export CMAKE_PREFIX_PATH=/afs/cern.ch/work/m/marcocle/workspace/LbScripts/LbUtils/cmake:$CMAKE_PREFIX_PATH

# ensure that Coverity is on the PATH
if [ -e /build/coverity/static-analysis/bin ] ; then
  export PATH=/build/coverity/static-analysis/bin:/build/coverity:$PATH
fi

set -xe
. setup.sh
day=$(date +%a)
timestamp=$(date -I)
deploybase=$(dirname /data/${ARTIFACTS_DIR})

# hard-coded because it may point to CVMFS
export LHCBNIGHTLIES=/afs/cern.ch/lhcb/software/nightlies

# remove old summaries
rm -rf $LHCBNIGHTLIES/www/logs/${slot}.${day}*

# create old-style progress stamp files
if [ -e $LHCBNIGHTLIES/${slot}/${day} ] ; then
  date +"%a %b %d %H:%M:%S %Y" > $LHCBNIGHTLIES/${slot}/${day}/isStarted-$platform
  echo ${slot}.${slot_build_id} >> $LHCBNIGHTLIES/${slot}/${day}/isStarted-$platform
  echo ${BUILD_URL} >> $LHCBNIGHTLIES/${slot}/${day}/isStarted-$platform
fi

if [ -e ${ARTIFACTS_DIR}/${slot}.json ] ; then
  config_file=${ARTIFACTS_DIR}/${slot}.json
else
  config_file=${ARTIFACTS_DIR}/configuration.xml#${slot}
fi

# create moving symlinks in the artifacts deployment directory (ASAP)
ssh buildlhcb.cern.ch "mkdir -pv ${deploybase} ; ln -svfT ${slot_build_id} ${deploybase}/${day} ; ln -svfT ${slot_build_id} ${deploybase}/${timestamp}"

if [ "${os_label}" = "coverity" ] ; then
  coverity_opt='--coverity'
fi

time BuildSlot.py --jobs 8 --timeout 18000 --build-id "{slot}.${slot_build_id}.{timestamp}" --artifacts-dir "${ARTIFACTS_DIR}" --rsync-dest "buildlhcb.cern.ch:${deploybase}/${slot_build_id}" --deploy-reports-to $LHCBNIGHTLIES/www/logs ${coverity_opt} ${config_file}

if [ -e $LHCBNIGHTLIES/${slot}/${day} ] ; then
  rm -f $LHCBNIGHTLIES/${slot}/${day}/isStarted-$platform
  date +"%a %b %d %H:%M:%S %Y" > $LHCBNIGHTLIES/${slot}/${day}/isDone-$platform
  echo ${slot}.${slot_build_id} >> $LHCBNIGHTLIES/${slot}/${day}/isDone-$platform
  echo ${BUILD_URL} >> $LHCBNIGHTLIES/${slot}/${day}/isDone-$platform
fi
