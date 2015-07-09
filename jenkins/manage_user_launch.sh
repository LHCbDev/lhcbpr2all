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

function manage_user_launch {

    local DESCRIPTION="DESCRIPTION : \
Function to manage slot launch by user"
    local USAGE="USAGE : \
manage_user_launch flavour slots
                [--slot-build-id <id>]
                [--no-checkout]
                [--rebuild-last-id]"

    local nb_param=0
    local slot_build_id_opt=""
    local no_checkout_opt=""
    local rebuild_last_id_opt=""

    while (( "$#" )); do
        if [[ "$1" =~ ^- ]] ; then
            case "$1" in
                "--slot-build-id")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 need an argument"
                        exit 3
                    else
                        local slot_build_id_opt="--slot-build-id $2"
                    fi
                    shift ;;

                "--no-checkout")
                    local no_checkout_opt="--no-checkout" ;;

                "--rebuild-last-id")
                    local rebuild_last_id_opt="--rebuild-last-id" ;;

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
                    local flavour="$1" ;;
                "1")
                    local slots="$1" ;;
                *)
                    echo "ERROR : Too much parameter"
                    echo ${USAGE}
                    exit 1
            esac
            local nb_param=$((nb_param+1))
        fi

        shift
    done

    if [ "${nb_param}" != "2" ] ; then
        echo "ERROR : Need more parameter"
        echo ${USAGE}
        exit 1
    fi

    if [ "${slot_build_id_opt}" != "" -a "${rebuild_last_id_opt}" != "" ] ; then
        echo "ERROR : $0 can't accept --slot-build-id and --rebuild-last-id"
        exit 1
    fi

    lbn-user-launch --verbose "${flavour}" "slot-params-{0}.txt" "${slots}" ${slot_build_id_opt} ${no_checkout_opt} ${rebuild_last_id_opt}

}

