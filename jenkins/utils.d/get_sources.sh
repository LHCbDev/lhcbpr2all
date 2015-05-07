function get_sources {

    if [ "$SET_COMMON" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON set with true"
	exit 1
    fi

    lbn-manage-rsync --verbose --get-sources "${RSYNC_DIR}" "${ARTIFACTS_DIR}"


    export GET_SOURCES="true"
}
