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

	local DESCRIPTION="DESCRIPTION : \
Function to check if we have precondition on an specify slot"
    local USAGE="USAGE : \
check_preconditions config_file slot slot_build_id
		[--platforms <platforms>]"

	local nb_param=0

	while (( "$#" )); do
		if [[ "$1" =~ 	^- ]] ; then
			case "$1" in
				"--platforms")
					if [[ "$2" = "" || "$2" =~ ^- ]] ; then
						echo "ERROR : Option $1 need an argument"
						exit 3
					else
						local platforms="$2"
					fi
					shift ;;

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
				"1")
					local slot="$1" ;;
				"2")
					local slot_build_id="$1" ;;
				*)
					echo "ERROR : Too much parameter"
					echo ${USAGE}
					exit 1
			esac
			local nb_param=$((nb_param+1))
		fi

		shift
    done

	if [ "${nb_param}" != "3" ] ; then
		echo "ERROR : Need more parameter"
		echo ${USAGE}
		exit 1
	fi

    if [ "$SET_COMMON" != "true" -o "$CONFIG_FILE_CHECKOUT" != "true" ] ; then
		echo "ERROR : $0 need SET_COMMON and CONFIG_FILE_CHECKOUT set with true"
		exit 1
    fi

	lbn-check-preconditions --verbose "${config}" "$slot" "$slot_build_id" ${platforms:+--platforms "${platforms}"}

}
