function push_artifact {

    local USAGE="push_artifact directory_src flavour slot slot_build_id "

    if [ $# != 4 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    local SOURCE="$1"
    local flavour="$2"
    local slot="$3"
    local slot_build_id="$4"

    local DESTINATION=$(get_remote_directory "$flavour" "$slot" "$slot_build_id")

    lbn-manage-remote --verbose "${SOURCE}" "${DESTINATION}"

}
