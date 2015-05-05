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

if [ "$JENKINS_MOCK" != "true" -o ! -e configs ] ; then
  # Get the slot configuration files from Subversion
  lbn-get-configs
fi

if [ "${slot}" = "lhcb-release" ] ; then
  if [ -z "${build_tool}" ] ; then
    build_tool=cmt
  fi
  if [ -n "${platforms}" ] ; then
    lbn-gen-release-config --build-tool="${build_tool}" --platforms="${platforms}" -o configs/${slot}.json --packages "${packages_list}" ${projects_list}
  else
    lbn-gen-release-config --build-tool="${build_tool}" -o configs/${slot}.json --packages "${packages_list}" ${projects_list}
  fi
fi

# this allow to bypass the configurations in SVN
if [ -e slot-config.json ] ; then
  cp -f -v slot-config.json configs/${slot}.json
fi

if [ -e configs/${slot}.json ] ; then
  config_file=configs/${slot}.json
else
  config_file=configs/configuration.xml#${slot}
fi

if [ "$JENKINS_MOCK" != "true" ] ; then
  submit_opt="--submit --flavour ${flavour}"
fi

if [ "${flavour}" = "release" ] ; then
  ignore_error_opt=--no-ignore-checkout-errors
fi

lbn-checkout --verbose --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}" ${submit_opt} ${ignore_error_opt} ${config_file}

# We need to copy the configuration at the end because
# StachCkeckout.py cleans the artifacts before starting
cp ${config_file%%#*} ${ARTIFACTS_DIR}
cp ${env_log} ${ARTIFACTS_DIR}
echo "$BUILD_URL" > ${ARTIFACTS_DIR}/checkout_job_url.txt

if [ "${flavour}" = "release" ] ; then
  # Now preparing the RPM with the project source
  time lbn-rpm --shared --verbose  --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}"  ${config_file}
  if [ -n "${packages_list}" ] ; then
    time lbn-rpm --datapkg --verbose  --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}"  ${config_file}
  fi
fi

lbn-rsync-push-artifact

lbn-check-preconditions --verbose ${config_file}

# Cleaning up
rm -rf tmp
