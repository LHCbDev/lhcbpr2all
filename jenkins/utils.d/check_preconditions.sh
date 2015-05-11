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

function check_preconditions {
      
    local USAGE="check_preconditions config_file slot slot_build_id [platforms]"

    if [ $# != 3 -a $# != 4  ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    if [ "$SET_COMMON" != "true" -o "$CONFIG_FILE_CHECKOUT" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON and CONFIG_FILE_CHECKOUT set with true"
	exit 1
    fi

    local config="$1"
    local slot="$2"
    local slot_build_id="$3"

    local platforms_opt=''
    if [ $# == 4 -a "$4" != "" ] ; then
	lbn-check-preconditions --verbose "${config}" "$slot" "$slot_build_id" --platforms "$4"
    else
    lbn-check-preconditions --verbose "${config}" "$slot" "$slot_build_id"
    fi

}
