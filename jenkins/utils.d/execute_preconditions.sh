function execute_preconditions {

    if [ "$SET_COMMON" != "true" -o "$GET_CONFIG_FILE" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON and GET_CONFIG_FILE set with true"
	exit 1
    fi

    lbn-preconditions --verbose ${config_file}
}