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

#
# Common set up for all the Jenkins scripts
#

function set_common {

    local DESCRIPTION="DESCRIPTION : \
Function to define common set up for all the Jenkins scripts"
    local USAGE="USAGE : \
set_common [--build] [--test]"

    local special_config=false

    while (( "$#" )); do
    if [[ "$1" =~ ^- ]] ; then
        case "$1" in
        "--build" | "--test" )
            local special_config=true ;;

        "-h" | "--help")
            echo ${DESCRIPTION}
            echo ${USAGE}
            exit 0;;

        *)
            echo "ERROR : Option $1 unknown in $0"
            echo "${USAGE}"
            exit 2
        esac
    else
        echo "ERROR : $0 doesn't have parameter"
        exit 1
    fi

    shift
    done

    # Need to set HOME on master because HOME not writable when connect by tomcat
    # Need to be FIX
    if [[ "${NODE_LABELS}" == *"master"* ]]
    then
        export HOME=$PWD
    fi

    export CMTCONFIG=${platform}
    # default (backward-compatible) build flavour
    if [ "${flavour}" == "" ] ; then
        export flavour=nightly
    fi

    # initial environment seen by the Jenkins script
    env_log=$(basename $0)${platform:+.}${platform}.env
    printenv | sort > ${env_log}

    # enforce C (POSIX) localization
    export LC_ALL=C

    # used by some tests to reduce the number of concurrent tests
    export LHCB_NIGHTLY_MAX_THREADS=1
    export WORKSPACE=${WORKSPACE:-$(readlink -e $(dirname ${BASH_SOURCE[0]})/../..)}
    export ARTIFACTS_DIR=${ARTIFACTS_DIR:-artifacts/${flavour}/${slot}/${slot_build_id}}
    mkdir -p ${ARTIFACTS_DIR}
    export RSYNC_SERVER=${RSYNC_SERVER:-lhcb-archive.cern.ch}
    export RSYNC_WORKDIR=${RSYNC_WORKDIR:-/data/archive/${ARTIFACTS_DIR}}
    export RSYNC_DIR=${RSYNC_DIR:-${RSYNC_SERVER}:${RSYNC_WORKDIR}}
    export TMPDIR=${WORKSPACE}/tmp
    mkdir -p ${TMPDIR}

    cp ${env_log} ${ARTIFACTS_DIR}

    echo ===================================================================
    echo Worker Node: $NODE_NAME
    echo Workspace: $WORKSPACE
    echo Artifacts dir: $ARTIFACTS_DIR
    echo ===================================================================

    LbScriptsVersion=prod

    # FIXME: workaround for LBCORE-769
    if ( echo $platform | grep -q slc5 ) ; then
        LbScriptsVersion=LBSCRIPTS_v8r3
    fi

    if [ "${special_config}" == "true" ] ; then
        export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH | tr : \\n | grep -v /gcc/ | tr \\n :)
        # FIXME: this is usually set by the "group login" script, but it is not
        #        called on lxbuild (it is needed to get the right ICC environment)
        export GROUP_DIR=/afs/cern.ch/group/z5
        export LOGIN_POST_SCRIPT=${GROUP_DIR}/post/login
        # FIXME: LbLogin cannot handle the special CMTCONFIG "*-test"
        . /cvmfs/lhcb.cern.ch/lib/lhcb/LBSCRIPTS/${LbScriptsVersion}/InstallArea/scripts/LbLogin.sh --no-cache -c ${platform/-test/-opt}
        #    export CMTCONFIG=${platform}
        # FIXME: path to the new gdb should be implicit in the build/run-time
        #        environment
        # See https://its.cern.ch/jira/browse/LBCORE-151
        export PATH=/afs/cern.ch/sw/lcg/external/gdb/7.6/$CMTOPT/bin:$PATH
        # COMPILER_PATH (set by LbLogin --no-cache) create troubles
        unset COMPILER_PATH

        # FIXME: we need to get the latest compilers wrappers until we release LbScripts
        export PATH=/afs/cern.ch/work/m/marcocle/workspace/LbScripts/LbUtils/scripts:$PATH
    else
        . /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/${LbScriptsVersion}/InstallArea/scripts/LbLogin.sh --no-cache
    fi

    # FIXME: pick up the latest CMT makefiles from the latest LbScripts on SLC5
    if ( echo $platform | grep -q slc5 ) ; then
        export LBCONFIGURATIONROOT=/afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/LbConfiguration
    fi

    # FIXME: workaround for the moving naming convention of CentOS 7 in LCG
    if [ "${os_label}" = "centos7" ] ; then
        export LCG_hostos=x86_64-cc7
    fi

# FIXME: on SLC5 LbScripts dev (LCG 68) does not get python (pick the system one)
    if [ $(python -c 'import sys; print "%d%d" % sys.version_info[:2]') = 24 ] ; then
        . SetupProject.sh LCGCMT 66 Python
    fi
# FIXME: partial installation of LCG cause wrong Python (system) on SLC6
    if [ $(python -c 'import sys; print "%d%d" % sys.version_info[:2]') = 26 ] ; then
        . SetupProject.sh LCGCMT 82 Python
    fi

    if klist -5 > /dev/null 2>&1 ; then
        kinit -R
        klist -5
    fi

    set -xe
    . $WORKSPACE/setup.sh

    export SET_COMMON=true
    if [ "${special_config}" == "true" ] ; then
        export SET_SPECIAL_CONFIG=true
    fi

}
