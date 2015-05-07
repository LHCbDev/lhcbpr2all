function push_artifact {

    USAGE="push_artifact directory_src flavour slot slot_build_id "

    if [ $# != 4 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    SOURCE="$1"
    flavour="$2"
    slot="$3"
    slot_build_id="$4"

    DESTINATION=$(get_remote_directory "$flavour" "$slot" "$slot_build_id")

    lbn-manage-rsync --verbose "${SOURCE}" "${DESTINATION}"

}
