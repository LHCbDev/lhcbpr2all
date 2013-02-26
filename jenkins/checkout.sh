#!/bin/bash
echo ===================================================================
echo Worker Node: $NODE_NAME
echo Workspace: $WORKSPACE
echo ===================================================================

. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh

set -xe
. setup.sh

svn cat -r "{"`date -I`"}" svn+ssh://svn.cern.ch/reps/lhcb/LHCbNightlyConf/trunk/configuration.xml > configuration.xml

if [ -e ${slot}.json ] ; then
  StackCheckout.py --verbose --build-id "{slot}.${slot_build_id}.{timestamp}" ${slot}.json
  mkdir -p sources
  cp ${slot}.json sources/${slot}.json
else
  StackCheckout.py --verbose --build-id "{slot}.${slot_build_id}.{timestamp}" configuration.xml#${slot}
  mkdir -p sources
  cp configuration.xml sources/configuration.xml
fi
