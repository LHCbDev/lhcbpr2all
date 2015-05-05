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

utils=$(dirname $0)/utils

# Set common environment
. $utils/set_common.sh
. $utils/get_configs_folder.sh
. $utils/checkout_slot.sh
. $utils/push_artifact.sh
. $utils/check_preconditions.sh


