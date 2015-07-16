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

export RSYNC_SERVER=${RSYNC_SERVER:-buildlhcb.cern.ch}
export RSYNC_WORKDIR=${RSYNC_WORKDIR:-/data/artifacts}

function get_remote_directory {

    local DESCRIPTION="DESCRIPTION : \
Function to get the remote directory on a slot with a flavour and slot_build_id"
    local USAGE="USAGE : \
get_directory_rsync flavour slot slot_build_id"

    local nb_param=0

    while (( "$#" )); do
        if [[ "$1" =~ ^- ]] ; then
            case "$1" in

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
                    local flavour="$1" ;;
                "1")
                    local slot="$1" ;;
                "2")
                    local slot_build_id="$1" ;;
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
        echo "ERROR : Need more parameters"
        echo ${USAGE}
        exit 1
    fi

    local RSYNC_DIR="${RSYNC_WORKDIR}/${flavour}/${slot}/${slot_build_id}"
    if [ ! -d "${RSYNC_DIR}" ] ; then
        local RSYNC_DIR="${RSYNC_SERVER}:${RSYNC_DIR}"
    fi

    echo "${RSYNC_DIR}"
}

function create_alias {

    local DESCRIPTION="DESCRIPTION : \
Function to create alias on the remote server"
    local USAGE="USAGE : \
create_alias"

    while (( "$#" )); do
        if [[ "$1" =~     ^- ]] ; then
            case "$1" in

                "-h" | "--help")
                    echo ${DESCRIPTION}
                    echo ${USAGE}
                    exit 0;;

                *)
                    echo "ERROR : Option $1 unknown in $0"
                    echo "${USAGE}"
                    exit 2
            esac
        else
            echo "ERROR : $0 doesn't have parameter"
            exit 1
        fi

        shift
    done

    local day=$(date +%a)
    local timestamp=$(date -I)
    local RSYNC_DIR="${RSYNC_WORKDIR}/${flavour}/${slot}"

    local COMMAND="mkdir -pv ${RSYNC_DIR} ; ln -svfT ${slot_build_id} ${RSYNC_DIR}/${day} ; ln -svfT ${slot_build_id} ${RSYNC_DIR}/${timestamp} ; ln -svfT ${slot_build_id} ${RSYNC_DIR}/Today"

    if [ ! -d "${RSYNC_WORKDIR}" ] ; then
        ssh ${RSYNC_SERVER} "${COMMAND}" || true
    else
        sh -c "${COMMAND}" || true
    fi

}
