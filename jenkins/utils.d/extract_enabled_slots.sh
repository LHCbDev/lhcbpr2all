function extract_enabled_slots {

    local USAGE="extract_enabled_slots flavour [slots]"

    if [ $# != 1 -a $# != 2 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    if [ "$SET_COMMON" != "true" -o "$GET_CONFIGS_FOLDER" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON and GET_CONFIGS_FOLDER set with true"
	exit 1
    fi

    local flavour="$1"
    local slots="$2"

    lbn-enabled-slots --verbose "${flavour}" "slot-params-{0}.txt" ${slots}

}

