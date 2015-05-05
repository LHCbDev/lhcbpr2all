function get_configs_folder {

    if [ "$JENKINS_MOCK" != "true" -o ! -e configs ] ; then
  # Get the slot configuration files from Subversion
	lbn-get-configs
    fi

    export GET_CONFIGS_FOLDER=true
}
