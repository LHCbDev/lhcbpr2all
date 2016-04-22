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
check_preconditions slot slot_build_id flavour
        [--platforms <platforms>]"

    local nb_param=0

    while (( "$#" )); do
        if [[ "$1" =~ ^- ]] ; then
            case "$1" in
                "--platforms")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 needs an argument"
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
                    echo "ERROR : Option $1 unknown in $0"
                    echo ${USAGE}
                    exit 2
            esac
        else
            case "${nb_param}" in
                "0")
                    local slot="$1" ;;
                "1")
                    local slot_build_id="$1" ;;
                "2")
                    local flavour="$1" ;;
                *)
                    echo "ERROR : Too many parameters"
                    echo ${USAGE}
                    exit 1
            esac
            local nb_param=$((nb_param+1))
        fi

        shift
    done

    if [ "${nb_param}" != "3" ] ; then
        echo "ERROR : Need 3 parameters"
        echo ${USAGE}
        exit 1
    fi

    if [ "$SET_COMMON" != "true" ] ; then
        echo "ERROR : $0 need SET_COMMON set to true"
        exit 1
    fi

    lbn-check-preconditions --verbose "$slot" "$slot_build_id" "$flavour" ${platforms:+--platforms "${platforms}"}

}
