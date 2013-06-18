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

# Set common environment
. $(dirname $0)/common.sh

# Get the slot configuration files from Subversion
lbn-get-configs

if [ -e configs/${slot}.json ] ; then
  config_file=configs/${slot}.json
else
  config_file=configs/configuration.xml#${slot}
fi

lbn-checkout --verbose --build-id "${slot}.${slot_build_id}.{timestamp}" --artifacts-dir "${ARTIFACTS_DIR}" --submit ${config_file}

# We need to copy the configuration at the end because
# StachCkeckout.py cleans the artifacts before starting
cp ${config_file%%#*} ${ARTIFACTS_DIR}
cp ${env_log} ${ARTIFACTS_DIR}
echo "$BUILD_URL" > ${ARTIFACTS_DIR}/checkout_job_url.txt
