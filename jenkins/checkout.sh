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

get_configs_folder --dest-dir "configs"

checkout_slot \
    "${flavour}" \
    "${slot}" \
    "${slot_build_id}" \
    --config-dir "configs" \
    --dest-dir "${ARTIFACTS_DIR}" \
    ${build_tool:+--build-tool "${build_tool}"} \
    ${paltforms:+--platforms "${platforms}"} \
    ${packages_list:+--packages-list "${packages_list}"} \
    ${projects_list:+--projects-list "${projects_list}"}

push_artifact \
    "${ARTIFACTS_DIR}" \
    "$(get_remote_directory "$flavour" "$slot" "$slot_build_id")"

check_preconditions \
    "${config_file_checkout}" \
    "${slot}" \
    "${slot_build_id}" \
    ${platforms:+--platforms "${platforms}"}


