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

if [ "$SET_COMMON" != "true" -o "$GET_CONFIG_FILE" != "true" ] ; then
    echo "ERROR : $0 need SET_COMMON and GET_CONFIG_FILE set with true"
    exit 1
fi

lbn-preconditions --verbose ${config_file}