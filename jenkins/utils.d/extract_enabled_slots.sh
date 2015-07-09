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

    local DESCRIPTION="DESCRIPTION : \
Function to extract all enabled slots from configs file"
    local USAGE="USAGE : \
extract_enabled_slots flavour
        [--config-dir <dir>]
        [--slots <slots>]"

    local nb_param=0
    local slots=""

    while (( "$#" )); do
        if [[ "$1" =~ ^- ]] ; then
            case "$1" in
                "--config-dir")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 need an argument"
                        exit 3
                    else
                        local config_dir_opt="--config-dir $2"
                    fi
                    shift ;;

                "--slots")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 need an argument"
                        exit 3
                    else
                        slots="$2"
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
                    local flavour="$1" ;;
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

    if [ "$SET_COMMON" != "true" -o "$GET_CONFIGS_FOLDER" != "true" ] ; then
        echo "ERROR : $0 need SET_COMMON and GET_CONFIGS_FOLDER set with true"
        exit 1
    fi

    lbn-enabled-slots --verbose ${config_dir_opt} "${flavour}" "slot-params-{0}.txt" ${slots:+--slots "${slots}"}

}

