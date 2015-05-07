function get_sources {
    
    USAGE="get_sources flavour slot slot_build_id directory_dest"

    if [ $# != 4 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    flavour="$1"
    slot="$2"
    slot_build_id="$3"
    DESTINATION="$4"

    SOURCE=$(get_remote_directory "$flavour" "$slot" "$slot_build_id")

    lbn-manage-rsync --verbose --get-sources "${SOURCE}" "${DESTINATION}"

    export GET_SOURCES="true"
}
