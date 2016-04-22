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

function push_artifact {

    local DESCRIPTION="DESCRIPTION : \
Function to push an artifact in a remote directory"
    local USAGE="USAGE : \
push_artifact source destination"

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
                    local source="$1" ;;
                "1")
                    local destination="$1" ;;
                *)
                    echo "ERROR : Too many parameters"
                    echo ${USAGE}
                    exit 1
            esac
            local nb_param=$((nb_param+1))
        fi

        shift
    done

    if [ "${nb_param}" != "2" ] ; then
        echo "ERROR : Need more parameters"
        echo ${USAGE}
        exit 1
    fi

    lbn-manage-remote --verbose "${source}" "${destination}"

}
