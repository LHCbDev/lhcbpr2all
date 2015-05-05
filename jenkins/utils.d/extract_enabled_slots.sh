function extract_enabled_slots {

    if [ "$SET_COMMON" != "true" -o "$GET_CONFIGS_FOLDER" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON and GET_CONFIGS_FOLDER set with true"
	exit 1
    fi

    lbn-enabled-slots --verbose 'slot-params-{0}.txt' ${slots}

}

