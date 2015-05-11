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

function execute_preconditions {

    local USAGE="execute_preconditions config_file"

    if [ $# != 1 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    if [ "$SET_COMMON" != "true" -o "$GET_CONFIG_FILE" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON and GET_CONFIG_FILE set with true"
	exit 1
    fi

    local config="$1"

    lbn-preconditions --verbose "${config}"
}