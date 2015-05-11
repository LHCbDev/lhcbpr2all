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

function extract_enabled_slots {

    local USAGE="extract_enabled_slots flavour [slots]"

    if [ $# != 1 -a $# != 2 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    if [ "$SET_COMMON" != "true" -o "$GET_CONFIGS_FOLDER" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON and GET_CONFIGS_FOLDER set with true"
	exit 1
    fi

    local flavour="$1"
    local slots="$2"

    lbn-enabled-slots --verbose "${flavour}" "slot-params-{0}.txt" ${slots}

}

