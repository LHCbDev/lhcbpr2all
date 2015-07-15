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

function get_configs_folder {

    DESCRIPTION="DESCRIPTION : \
Function to get the config folder"
    USAGE="USAGE : \
get_config_folder [--dest-dir <dir>]"

    local dest_dir="."

    while (( "$#" )); do
        if [[ "$1" =~ ^- ]] ; then
            case "$1" in
                "--dest-dir")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 needs an argument"
                        exit 3
                    else
                        local dest_dir="$2"
                    fi
                    shift ;;

                "-h" | "--help")
                    echo ${DESCRIPTION}
                    echo ${USAGE}
                    exit 0;;
                *)
                    echo "ERROR : Option $1 unknown in $0"
                    echo "${USAGE}"
                    exit 1
            esac
        else
            echo "ERROR : $0 doesn't have parameter"
        fi

        shift
    done

    if [ "$JENKINS_MOCK" != "true" -o ! -e configs ] ; then
        svn export http://svn.cern.ch/guest/lhcb/LHCbNightlyConf/trunk --force "${dest_dir}"
    fi

    export GET_CONFIGS_FOLDER=true
}
