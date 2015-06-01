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

if [ "${rebuild_last_id}" == "true" ] ; then
    {rebuild_last_id_opt="--rebuild-last-id"
fi

if [ "${no_checkout}" == "true" ] ; then
    no_checkout_opt="--no-checkout"
fi

manage_user_launch \
    "${flavour}" \
    "${slots}" \
    ${slot_build_id:+--slot-build-id "${slot_build_id}"} \
    ${rebuild_last_id_opt} \
    ${no_checkout_opt}
