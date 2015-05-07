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

. $(dirname $0)/utils.sh

# Set common environment
set_common
get_configs_folder
checkout_slot \
    "${flavour}" \
    "${slot}" \
    "${slot_build_id}" \
    "${ARTIFACTS_DIR}" \
    "${build_tool}" \
    "${platforms}" \
    "${packages_list}" \
    "${peojects_list}"

push_artifact "${ARTIFACTS_DIR}" "${flavour}" "${slot}" "${slot_build_id}"
check_preconditions "${config_file_checkout}"


