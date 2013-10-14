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

# enforce C (POSIX) localization
export LC_ALL=C

# used by some tests to reduce the number of concurrent tests
export LHCB_NIGHTLY_MAX_THREADS=1

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
  # FIXME: this is usually set by the "group login" script, but it is not
  #        called on lxbuild (it is needed to get the right ICC environment)
  export LOGIN_POST_SCRIPT=/afs/cern.ch/group/z5/post/login
  . /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh -c ${platform}
  # FIXME: path to the new gdb should be implicit in the build/run-time
  #        environment
  # See https://its.cern.ch/jira/browse/LBCORE-151
  export PATH=/afs/cern.ch/sw/lcg/external/gdb/7.6/$CMTOPT/bin:$PATH
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
