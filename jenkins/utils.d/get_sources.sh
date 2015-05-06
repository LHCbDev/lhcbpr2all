function get_sources {

    if [ "$SET_COMMON" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON set with true"
	exit 1
    fi

    lbn-manage-rsync --verbose --get-sources --source "${RSYNC_DIR}" --destination "${ARTIFACTS_DIR}"


    export GET_SOURCES="true"
}
