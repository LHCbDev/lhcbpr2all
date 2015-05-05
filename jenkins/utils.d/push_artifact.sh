function push_artifact {

    if [ "$SET_COMMON" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON set with true"
	exit 1
    fi

    lbn-manage-rsync --verbose --progress --source "${ARTIFACTS_DIR}" --destination "${RSYNC_DIR}"

}
