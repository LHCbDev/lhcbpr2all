###############################################################################
# (c) Copyright 2013 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################

function build_slot {

	local DESCRIPTION="DESCRIPTION : \
Function to build a slot on a specify platform"
    local USAGE="USAGE : \
build_slot flavour slot slot_build_id platform
		[--build-dir <dir>] 
		[--os-label <label>]"

	local nb_param=0

	while (( "$#" )); do
		if [[ "$1" =~ 	^- ]] ; then
			case "$1" in
				"--build-dir")
					if [[ "$2" = "" || "$2" =~ ^- ]] ; then
						echo "ERROR : Option $1 need an argument"
						exit 3
					else
						local directory="$2"
					fi
					shift ;;

				"--os-label")
					if [[ "$2" = "" || "$2" =~ ^- ]] ; then
						echo "ERROR : Option $1 need an argument"
						exit 3
					else
						local os_label="$2"
					fi
					shift ;;

				"-h" | "--help")
					echo ${DESCRIPTION}
					echo ${USAGE}
					exit 0;;
				*)
					echo "ERROR : Option $1 unknow in $0"
					echo ${USAGE}
					exit 2
			esac
		else
			case "${nb_param}" in
				"0")
					local flavour="$1" ;;
				"1")
					local slot="$1" ;;
				"2")
					local slot_build_id="$1" ;;
				"3")
					local platform="$1" ;;
				*)
					echo "ERROR : Too much parameter"
					echo ${USAGE}
					exit 1
			esac
			local nb_param=$((nb_param+1))
		fi

		shift
    done

	if [ "${nb_param}" != "4" ] ; then
		echo "ERROR : Need more parameter"
		echo ${USAGE}
		exit 1
	fi

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

    local config_file=${directory}/slot-config.json

    if [ "${os_label}" = "coverity" ] ; then
		coverity_opt='--coverity'
	  # Coverity builds to not need to trigger tests
		with_tests=no
    fi

    if [ "$JENKINS_MOCK" != "true" ] ; then
	  # create moving symlinks in the artifacts deployment directory (ASAP)
	  # (ignore errors, see <https://its.cern.ch/jira/browse/LBCORE-153>)
		create_alias
		submit_opt="--submit --flavour ${flavour}"
		rsync_opt="--rsync-dest $(get_remote_directory "$flavour" "$slot" "$slot_build_id")"
    fi

# Notify the system of the builds that need to be tested.
    if [ "${with_tests}" != "no" ] ; then
		lbn-list-expected-builds --slot-build-id ${slot_build_id} --build-id "${slot}.${slot_build_id}" --artifacts-dir "${directory}" --platforms "${platform}" -o expected_builds.json ${config_file}
		if [ "$JENKINS_MOCK" != "true" ] ; then
			datadir=${JENKINS_HOME}/nightlies/${flavour}/running_builds
			scp expected_builds.json buildlhcb.cern.ch:${datadir}/expected_builds.${slot}.${slot_build_id}.${platform}.json
		fi
    fi

    time lbn-build --no-distcc --verbose --jobs 8 --timeout 18000 --build-id "${slot}.${slot_build_id}" --artifacts-dir "${directory}" --clean ${submit_opt} ${rsync_opt} ${coverity_opt} ${config_file}

    if [ "${flavour}" = "release" ] ; then
	  # Prepare the RPMs
		time lbn-rpm --verbose  --build-id "${slot}.${slot_build_id}" --artifacts-dir "${directory}"  ${config_file} --platform "${platform}"
    fi

    if [ "$JENKINS_MOCK" != "true" ] ; then
		push_artifact "${directory}" "$(get_remote_directory "$flavour" "$slot" "$slot_build_id")"
    fi

# if possible and requested, generate glimpse indexes and upload them to buildlhcb
    if [ "${flavour}" = "release" -o -n "${run_indexer}" ] ; then
		if which glimpseindex &> /dev/null ; then 
		  # clean up the build dir before indexing
			lbn-build --verbose --clean --build-id "${slot}.${slot_build_id}" --artifacts-dir "${directory}" --clean ${config_file}
			time lbn-index --verbose --build-id "${slot}.${slot_build_id}" --artifacts-dir "${directory}" ${config_file}
			if [ "${flavour}" = "release" ] ; then
			time lbn-rpm --glimpse --verbose  --build-id "${slot}.${slot_build_id}" --artifacts-dir "${directory}"  ${config_file}
			fi
			if [ "$JENKINS_MOCK" != "true" ] ; then
			push_artifact "${directory}" "$(get_remote_directory "$flavour" "$slot" "$slot_build_id")"
			fi
		fi
    fi

    if [ "$JENKINS_MOCK" != "true" ] ; then
	  # Clean up
		rm -rf ${directory} build
    fi

}
