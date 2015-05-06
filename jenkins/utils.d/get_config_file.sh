function get_config_file {

    if [ "$SET_COMMON" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON set with true"
	exit 1
    fi

    SOURCES="${RSYNC_DIR}"
    if [ -d "${RSYNC_WORKDIR}" ] ; then
	SOURCES="${RSYNC_WORKDIR}"
    fi

    lbn-manage-rsync --verbose --get-config --source "${SOURCES}" --destination "${ARTIFACTS_DIR}"

    if [ -e ${ARTIFACTS_DIR}/${slot}.json ] ; then
	export config_file=${ARTIFACTS_DIR}/${slot}.json
    else
	export config_file=${ARTIFACTS_DIR}/configuration.xml#${slot}
    fi

    export GET_CONFIG_FILE="true"
}