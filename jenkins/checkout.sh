#!/bin/bash
echo ===================================================================
echo Worker Node: $NODE_NAME
echo Workspace: $WORKSPACE
echo ===================================================================

. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh

set -xe
. setup.sh

svn cat -r "{"`date -I`"}" svn+ssh://svn.cern.ch/reps/lhcb/LHCbNightlyConf/trunk/configuration.xml > configuration.xml

mkdir -p sources
if [ -e ${slot}.json ] ; then
  cp ${slot}.json sources/${slot}.json
  config_file=${slot}.json
else
  cp configuration.xml sources/configuration.xml
  config_file=configuration.xml#${slot}
fi

StackCheckout.py --verbose --build-id "{slot}.${slot_build_id}.{timestamp}" --artifacts-dir "artifacts/{slot}/${slot_build_id}" ${config_file}
