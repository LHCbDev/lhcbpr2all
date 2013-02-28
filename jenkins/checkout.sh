#!/bin/bash
echo ===================================================================
echo Worker Node: $NODE_NAME
echo Workspace: $WORKSPACE
echo ===================================================================

. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh

set -xe
. setup.sh

mkdir -p artifacts/${slot}/${slot_build_id}
svn cat -r "{"`date -I`"}" svn+ssh://svn.cern.ch/reps/lhcb/LHCbNightlyConf/trunk/configuration.xml > artifacts/${slot}/${slot_build_id}/configuration.xml

if [ -e ${slot}.json ] ; then
  cp ${slot}.json artifacts/${slot}/${slot_build_id}/${slot}.json
  config_file=artifacts/${slot}/${slot_build_id}/${slot}.json
else
  config_file=artifacts/${slot}/${slot_build_id}/configuration.xml#${slot}
fi

StackCheckout.py --verbose --build-id "{slot}.${slot_build_id}.{timestamp}" --artifacts-dir "artifacts/{slot}/${slot_build_id}" ${config_file}
