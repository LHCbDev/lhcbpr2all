function build_slot {

    if [ "$SET_COMMON" != "true" -o "$GET_CONFIG_FILE" != "true" -o "$GET_SOURCES" != "true" -o "$SET_SPECIAL_CONFIG" != "true" ] ; then
	echo "ERROR : $0 need SET_COMMON, SET_SPECIAL_CONFIG, GET_SOURCES and GET_CONFIG_FILE set with true"
	exit 1
    fi

    export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH | tr : \\n | grep -v /gcc/ | tr \\n :)

    day=$(date +%a)
    timestamp=$(date -I)
    deploybase=$(dirname ${RSYNC_WORKDIR})

# special hack to get a dev version of the CMake configuration files
    export CMAKE_PREFIX_PATH=/afs/cern.ch/work/m/marcocle/workspace/LbScripts/LbUtils/cmake:$CMAKE_PREFIX_PATH

# ensure that the distcc lock directory exists
    if [ -n "$DISTCC_DIR" ] ; then
	mkdir -pv $DISTCC_DIR
    fi

# ensure that Coverity is on the PATH
    if [ -e /build/coverity/static-analysis/bin ] ; then
	export PATH=/build/coverity/static-analysis/bin:/build/coverity:$PATH
    fi

    config_file=${ARTIFACTS_DIR}/slot-config.json

    if [ "${os_label}" = "coverity" ] ; then
	coverity_opt='--coverity'
  # Coverity builds to not need to trigger tests
	with_tests=no
    fi

    if [ "$JENKINS_MOCK" != "true" ] ; then
  # create moving symlinks in the artifacts deployment directory (ASAP)
  # (ignore errors, see <https://its.cern.ch/jira/browse/LBCORE-153>)
	ssh "${RSYNC_SERVER}" "mkdir -pv ${deploybase} ; ln -svfT ${slot_build_id} ${deploybase}/${day} ; ln -svfT ${slot_build_id} ${deploybase}/${timestamp}" || true

	submit_opt="--submit --flavour ${flavour}"
	rsync_opt="--rsync-dest '${RSYNC_DIR}'"
    fi

# Notify the system of the builds that need to be tested.
    if [ "${with_tests}" != "no" ] ; then
	lbn-list-expected-builds --slot-build-id ${slot_build_id} --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}" --platforms "${platform}" -o expected_builds.json ${config_file}
	if [ "$JENKINS_MOCK" != "true" ] ; then
	    datadir=${JENKINS_HOME}/nightlies/${flavour}/running_builds
	    scp expected_builds.json buildlhcb.cern.ch:${datadir}/expected_builds.${slot}.${slot_build_id}.${platform}.json
	fi
    fi

    time lbn-build --no-distcc --verbose --jobs 8 --timeout 18000 --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}" --clean ${submit_opt} ${rsync_opt} ${coverity_opt} ${config_file}

    if [ "${flavour}" = "release" ] ; then
  # Prepare the RPMs
	time lbn-rpm --verbose  --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}"  ${config_file} --platform "${platform}"
    fi

    if [ "$JENKINS_MOCK" != "true" ] ; then
	push_artifact
    fi

# if possible and requested, generate glimpse indexes and upload them to buildlhcb
    if [ "${flavour}" = "release" -o -n "${run_indexer}" ] ; then
	if which glimpseindex &> /dev/null ; then 
      # clean up the build dir before indexing
	    lbn-build --verbose --clean --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}" --clean ${config_file}
	    time lbn-index --verbose --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}" ${config_file}
	    if [ "${flavour}" = "release" ] ; then
		time lbn-rpm --glimpse --verbose  --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}"  ${config_file}
	    fi
	    if [ "$JENKINS_MOCK" != "true" ] ; then
		push_artifact
	    fi
	fi
    fi

    if [ "$JENKINS_MOCK" != "true" ] ; then
  # Clean up
	rm -rf ${ARTIFACTS_DIR} build
    fi

}