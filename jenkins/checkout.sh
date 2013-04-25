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

. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh

set -xe
. setup.sh

# Get the slot configuration files from Subversion
svn export svn+ssh://svn.cern.ch/reps/lhcb/LHCbNightlyConf/trunk tmpconfig

if [ -e tmpconfig/${slot}.json ] ; then
  config_file=tmpconfig/${slot}.json
else
  config_file=tmpconfig/configuration.xml#${slot}
fi

StackCheckout.py --verbose --build-id "{slot}.${slot_build_id}.{timestamp}" --artifacts-dir "${ARTIFACTS_DIR}" ${config_file}

# We need to copy the configuration at the end because
# StachCkeckout.py cleans the artifacts before starting
cp ${config_file%%#*} ${ARTIFACTS_DIR}
