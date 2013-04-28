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

#
# Common set up for all the Jenkins scripts
#

# initial environment seen by the Jenkins script
env_log=$(basename $0)${platform:+.}${platform}.env
printenv | sort > ${env_log}

export ARTIFACTS_DIR=${ARTIFACTS_DIR:-artifacts/${slot}/${slot_build_id}}
mkdir -p ${ARTIFACTS_DIR}
export TMPDIR=${WORKSPACE}/tmp
mkdir -p ${TMPDIR}

cp ${env_log} ${ARTIFACTS_DIR}

echo ===================================================================
echo Worker Node: $NODE_NAME
echo Workspace: $WORKSPACE
echo Artifacts dir: $ARTIFACTS_DIR
echo ===================================================================

if [ -n "${set_config}" ] ; then
  . /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh -c ${platform}
else
  . /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh
fi

if [ -e ${ARTIFACTS_DIR}/${slot}.json ] ; then
  config_file=${ARTIFACTS_DIR}/${slot}.json
else
  config_file=${ARTIFACTS_DIR}/configuration.xml#${slot}
fi

if klist -5 > /dev/null 2>&1 ; then
  kinit -R
  klist -5
fi

set -xe
. setup.sh
