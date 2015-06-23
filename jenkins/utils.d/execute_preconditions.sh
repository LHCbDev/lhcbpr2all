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

	local DESCRIPTION="DESCRIPTION : \
Function to execute precondition contain in a specify file"
    local USAGE="USAGE : \
execute_preconditions config_file"

	local nb_param=0

    while (( "$#" )); do
		if [[ "$1" =~ 	^- ]] ; then
			case "$1" in
				"-h" | "--help")
					echo ${DESCRIPTION}
					echo ${USAGE}
					exit 0;;
				*)
					echo "ERROR : Option $1 unknow in $0"
					echo ${USAGE}
					exit 2
			esac
		else
			case "${nb_param}" in
				"0")
					local config="$1" ;;
				*)
					echo "ERROR : Too much parameter"
					echo ${USAGE}
					exit 1
			esac
			local nb_param=$((nb_param+1))
		fi

		shift
    done

	if [ "${nb_param}" != "1" ] ; then
		echo "ERROR : Need more parameter"
		echo ${USAGE}
		exit 1
	fi

    if [ "$SET_COMMON" != "true" -o "$GET_CONFIG_FILE" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON and GET_CONFIG_FILE set with true"
	exit 1
    fi

    lbn-preconditions --verbose "${config}"
}
