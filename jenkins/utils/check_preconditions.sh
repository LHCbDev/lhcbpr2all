#!/bin/sh
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

# Script to launch check_preconditions python script

if [ "$SET_COMMON" != "true" -o "$CONFIG_FILE_CHECKOUT" != "true" ] ; then
    echo "ERROR : $0 need SET_COMMON and CONFIG_FILE_CHECKOUT set with true"
    exit 1
fi

lbn-check-preconditions --verbose ${config_file_checkout}