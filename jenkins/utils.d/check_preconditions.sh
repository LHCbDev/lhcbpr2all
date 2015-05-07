function check_preconditions {
      
    local USAGE="check_preconditions config_file"

    if [ $# != 1 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    if [ "$SET_COMMON" != "true" -o "$CONFIG_FILE_CHECKOUT" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON and CONFIG_FILE_CHECKOUT set with true"
	exit 1
    fi

    local config="$1"

    lbn-check-preconditions --verbose "${config}"
}
