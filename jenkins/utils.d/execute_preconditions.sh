function execute_preconditions {

    local USAGE="execute_preconditions config_file"

    if [ $# != 1 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    if [ "$SET_COMMON" != "true" -o "$GET_CONFIG_FILE" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON and GET_CONFIG_FILE set with true"
	exit 1
    fi

    local config="$1"

    lbn-preconditions --verbose "${config}"
}