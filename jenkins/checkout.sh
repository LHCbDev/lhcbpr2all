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
timestamp=$(date -I)

if [ "$JENKINS_MOCK" != "true" -o ! -e configs ] ; then
  # Get the slot configuration files from Subversion
  lbn-get-configs
fi

if [ "${slot}" = "lhcb-release" ] ; then
  if [ -n "${platforms}" ] ; then
    lbn-gen-release-config --cmt --platforms="${platforms}" -o configs/${slot}.json ${projects_list}
  else
    lbn-gen-release-config --cmt -o configs/${slot}.json ${projects_list}
  fi
fi

if [ -e configs/${slot}.json ] ; then
  config_file=configs/${slot}.json
else
  config_file=configs/configuration.xml#${slot}
fi

if [ "$JENKINS_MOCK" != "true" ] ; then
  submit_opt="--submit --flavour ${flavour}"
fi

lbn-checkout --verbose --build-id "${slot}.${slot_build_id}.{timestamp}" --artifacts-dir "${ARTIFACTS_DIR}" ${submit_opt} ${config_file}

# We need to copy the configuration at the end because
# StachCkeckout.py cleans the artifacts before starting
cp ${config_file%%#*} ${ARTIFACTS_DIR}
cp ${env_log} ${ARTIFACTS_DIR}
echo "$BUILD_URL" > ${ARTIFACTS_DIR}/checkout_job_url.txt

if [ "${flavour}" = "release" ] ; then
  # Now preparing the RPM with the project source
  time lbn-rpm --shared --verbose  --build-id "${slot}.${slot_build_id}.${timestamp}" --artifacts-dir "${ARTIFACTS_DIR}"  ${config_file}
fi

# Cleaning up
rm -rf tmp
