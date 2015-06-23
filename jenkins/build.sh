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

set_common --build

get_artifact \
	--get-config \
	--get-sources \
    "$(get_remote_directory "$flavour" "$slot" "$slot_build_id")" \
    "${ARTIFACTS_DIR}"

build_slot \
    "${flavour}" \
    "${slot}" \
    "${slot_build_id}" \
    "${platform}" \
    --build-dir "${ARTIFACTS_DIR}" \
    ${os_label:+--os-label "${os_label}"}
