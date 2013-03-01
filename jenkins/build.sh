#!/bin/bash
echo ===================================================================
echo Worker Node: $NODE_NAME
echo Workspace: $WORKSPACE
echo ===================================================================

. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh -c $platform

export CMAKE_PREFIX_PATH=/afs/cern.ch/work/m/marcocle/workspace/LbScripts/LbUtils/cmake:$CMAKE_PREFIX_PATH

set -xe
. setup.sh
day=$(date +%a)
timestamp=$(date -I)

# hard-coded because it may point to CVMFS
export LHCBNIGHTLIES=/afs/cern.ch/lhcb/software/nightlies

# remove old summaries
rm -rf $LHCBNIGHTLIES/www/logs/${slot}.${day}*

# create old-style progress stamp files
if [ -e $LHCBNIGHTLIES/${slot}/${day} ] ; then
  date +"%a %b %d %H:%M:%S %Y" > $LHCBNIGHTLIES/${slot}/${day}/isStarted-$platform
  echo ${slot}.${slot_build_id} >> $LHCBNIGHTLIES/${slot}/${day}/isStarted-$platform
fi

if [ -e artifacts/${slot}/${slot_build_id}/${slot}.json ] ; then
  config_file=artifacts/${slot}/${slot_build_id}/${slot}.json
else
  config_file=artifacts/${slot}/${slot_build_id}/configuration.xml#${slot}
fi

deploybase=/data/artifacts/${slot}
# create moving symlinks in the artifacts deployment directory (ASAP)
ssh buildlhcb.cern.ch "ln -svfT ${slot_build_id} ${deploybase}/${day} ; ln -svfT ${slot_build_id} ${deploybase}/${timestamp}"

time BuildSlot.py --jobs 8 --timeout 18000 --build-id "{slot}.${slot_build_id}.{timestamp}" --artifacts-dir "artifacts/{slot}/${slot_build_id}" --rsync-dest "buildlhcb.cern.ch:${deploybase}/${slot_build_id}" --deploy-reports-to $LHCBNIGHTLIES/www/logs ${config_file}

if [ -e $LHCBNIGHTLIES/${slot}/${day} ] ; then
  rm -f $LHCBNIGHTLIES/${slot}/${day}/isStarted-$platform
  date +"%a %b %d %H:%M:%S %Y" > $LHCBNIGHTLIES/${slot}/${day}/isDone-$platform
  echo ${slot}.${slot_build_id} >> $LHCBNIGHTLIES/${slot}/${day}/isDone-$platform
fi
