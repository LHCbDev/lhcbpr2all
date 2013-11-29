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

# Clean LD_LIBRARY_PATH of /gcc/ entries
# (see comment on issue LBCORE-109 http://cern.ch/go/PLQ7)
export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH | tr : \\n | grep -v /gcc/ | tr \\n :)

# Set common environment
set_config=1
. $(dirname $0)/common.sh

day=$(date +%a)
timestamp=$(date -I)
deploybase=$(dirname /data/${ARTIFACTS_DIR})

# special hack to get a dev version of the CMake configuration files
export CMAKE_PREFIX_PATH=/afs/cern.ch/work/m/marcocle/workspace/LbScripts/LbUtils/cmake:$CMAKE_PREFIX_PATH

if [ "$JENKINS_MOCK" = "true" ] ; then
  prepare_opt="--clean"
  config_file=${ARTIFACTS_DIR}/slot-config.json
else
  if [ "$JOB_NAME" = "nightly-test-slot-test-project-platform" ] ; then
    artifacts_root_opt="--artifacts-root https://buildlhcb.cern.ch/artifacts/testing"
  fi
  submit_opt="--submit --cdash-submit"
  rsync_opt="--rsync-dest buildlhcb.cern.ch:${deploybase}/${slot_build_id}"

  lbn-install --verbose ${artifacts_root_opt} --dest build --projects ${project} --platforms ${platform} ${slot} ${slot_build_id}
  prepare_opt="--no-unpack"
  config_file=build/slot-config.json
fi

time lbn-build --verbose --jobs 8 --timeout 18000 --build-id "${slot}.${slot_build_id}.{timestamp}" --artifacts-dir "${ARTIFACTS_DIR}" --tests-only --projects ${project} ${prepare_opt} ${submit_opt} ${rsync_opt} ${coverity_opt} ${config_file}

if [ "$JENKINS_MOCK" != "true" ] ; then
  # Clean up
  rm -rf ${ARTIFACTS_DIR} build
fi
