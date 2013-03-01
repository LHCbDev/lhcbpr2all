#!/bin/bash
echo ===================================================================
echo Worker Node: $NODE_NAME
echo Workspace: $WORKSPACE
echo ===================================================================

. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh

set -xe
. setup.sh

if [ -e ${slot}.json ] ; then
  config_file=${slot}.json
else
  svn cat -r "{"`date -I`"}" svn+ssh://svn.cern.ch/reps/lhcb/LHCbNightlyConf/trunk/configuration.xml > configuration.xml
  config_file=configuration.xml#${slot}
fi

StackCheckout.py --verbose --build-id "{slot}.${slot_build_id}.{timestamp}" --artifacts-dir "artifacts/{slot}/${slot_build_id}" ${config_file}

# We need to copy the configuration at the end because
# StachCkeckout.py cleans the artifacts before starting
cp ${config_file%%#*} artifacts/${slot}/${slot_build_id}
