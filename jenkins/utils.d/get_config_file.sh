function get_config_file {

    USAGE="get_config_file flavour slot slot_build_id directory_dest"

    if [ $# != 4 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    flavour="$1"
    slot="$2"
    slot_build_id="$3"
    DESTINATION="$4"

    SOURCE=$(get_remote_directory "$flavour" "$slot" "$slot_build_id")

    lbn-manage-rsync --verbose --get-config "${SOURCE}" "${DESTINATION}"

    if [ -e ${DESTINATION}/${slot}.json ] ; then
	export config_file=${DESTINATION}/${slot}.json
    else
	export config_file=${DESTINATION}/configuration.xml#${slot}
    fi

    export GET_CONFIG_FILE="true"
}