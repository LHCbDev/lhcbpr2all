function get_artifact {

    local DESCRIPTION="DESCRIPTION : \
Function to get a directory from a remote directory"
    local USAGE="USAGE : \
get_config_file source destination
        [--get-config]
        [--get-sources]"

    local nb_param=0

    while (( "$#" )); do
        if [[ "$1" =~ ^- ]] ; then
            case "$1" in
                "--get-config")
                    local get_config="--get-config";;

                "--get-sources")
                    local get_sources="--get-sources";;

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
                    local source="$1" ;;
                "1")
                    local destination="$1" ;;
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

    lbn-manage-remote --verbose ${get_config} ${get_sources} "${source}" "${destination}"

    if [ "${get_config}" != "" ] ; then
        if [ -e ${destination}/${slot}.json ] ; then
            export config_file=${destination}/${slot}.json
        else
            export config_file=${destination}/configuration.xml#${slot}
        fi
        export GET_CONFIG_FILE="true"
    fi

}
