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

function checkout_slot {

    loglevel_opt="--debug"


    local DESCRIPTION="DESCRIPTION : \
Function to checkout a specific slot"
    local USAGE="USAGE : \
checkout_slot flavour slot slot_build_id
                [--config-dir <dir>]
                [--dest-dir <dir>]
                [--build-tool <tool>]
                [--platforms <platforms>]
                [--packages-list <packages>]
                [--peojects-list <projects>]
                [--no-checkout]"

    local nb_param=0
    local config_dir="."
    local dest_dir="."
    local no_checkout=false

    while (( "$#" )); do
        if [[ "$1" =~ ^- ]] ; then
            case "$1" in
                "--config-dir")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 need an argument"
                        exit 3
                    else
                        local config_dir="$2"
                    fi
                    shift ;;

                "--dest-dir")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 need an argument"
                        exit 3
                    else
                        local dest_dir="$2"
                    fi
                    shift ;;

                "--build-tool")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 need an argument"
                        exit 3
                    else
                        local build_tool="$2"
                    fi
                    shift ;;

                "--platforms")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 need an argument"
                        exit 3
                    else
                        local platforms="$2"
                    fi
                    shift ;;

                "--packages-list")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 need an argument"
                        exit 3
                    else
                        local packages_list="$2"
                    fi
                    shift ;;

                "--projects-list")
                    if [[ "$2" = "" || "$2" =~ ^- ]] ; then
                        echo "ERROR : Option $1 need an argument"
                        exit 3
                    else
                        local projects_list="$2"
                    fi
                    shift ;;

                "--no-checkout")
                    local no_checkout=true ;;

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

    if [ "${no_checkout}" != "true" ]; then
        if [ "${nb_param}" != "3" ] ; then
            echo "ERROR : Need more parameter"
            echo ${USAGE}
            exit 1
        fi

        if [ "$SET_COMMON" != "true" -o "$GET_CONFIGS_FOLDER" != "true" ] ; then
            echo "ERROR : $0 need SET_COMMON and GET_CONFIGS_FOLDER set with true"
            exit 1
        fi

        if [ "${slot}" = "lhcb-release" ] ; then
            if [ -z "${build_tool}" ] ; then
                build_tool=cmt
            fi
            if [ -n "${platforms}" ] ; then
                lbn-gen-release-config --build-tool="${build_tool}" --platforms="${platforms}" -o configs/${slot}.json --packages "${packages_list}" ${projects_list}
            else
                lbn-gen-release-config --build-tool="${build_tool}" -o configs/${slot}.json --packages "${packages_list}" ${projects_list}
            fi
        fi

        # this allow to bypass the configurations in SVN
        if [ -e slot-config.json ] ; then
            cp -f -v slot-config.json "${config_dir}/${slot}.json"
        fi

    fi

    if [ -e "${config_dir}/${slot}.json" ] ; then
        config_file_checkout="${config_dir}/${slot}.json"
    else
        config_file_checkout="${config_dir}/configuration.xml#${slot}"
    fi

    if  [ "${no_checkout}" != "true" ]; then

        if [ "$JENKINS_MOCK" != "true" ] ; then
            submit_opt="--submit --flavour ${flavour}"
        fi

        if [ "${flavour}" = "release" ] ; then
            ignore_error_opt=--no-ignore-checkout-errors
        fi

        lbn-checkout ${loglevel_opt} --build-id "${slot}.${slot_build_id}" --artifacts-dir "${dest_dir}" ${submit_opt} ${ignore_error_opt} ${config_file_checkout}

        # We need to copy the configuration at the end because
        # StachCkeckout.py cleans the artifacts before starting
        cp ${config_file_checkout%%#*} ${dest_dir}
        cp ${env_log} ${dest_dir}
        echo "$BUILD_URL" > ${dest_dir}/checkout_job_url.txt

        if [ "${flavour}" = "release" ] ; then
            # Now preparing the RPM with the project source
            time lbn-rpm --shared ${loglevel_opt} --build-id "${slot}.${slot_build_id}" --artifacts-dir "${dest_dir}"  ${config_file_checkout}
            if [ -n "${packages_list}" ] ; then
                time lbn-rpm --datapkg ${loglevel_opt}  --build-id "${slot}.${slot_build_id}" --artifacts-dir "${dest_dir}"  ${config_file_checkout}
            fi
        fi

        rm -rf tmp

    fi

    export config_file_checkout=${config_file_checkout}
    export CONFIG_FILE_CHECKOUT=true

}
