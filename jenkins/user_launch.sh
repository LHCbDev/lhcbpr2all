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

set_common

get_configs_folder --dest-dir "configs"

extract_enabled_slots \
    "${flavour}" \
    "${slots}"} \
    ${slot_build_id:+--slot-build-id "${slot_build_id}"} \
    ${rebuild_last_id:+--rebuild-last-id} \
    ${no_checkout:+--no-checkout}
