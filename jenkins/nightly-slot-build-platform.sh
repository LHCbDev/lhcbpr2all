#!/bin/bash
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

. $(dirname $0)/utils.sh

set_common --build

if [ "$JENKINS_MOCK" != "true" ] ; then
    get_artifact \
        --get-config \
        --get-sources \
        "$(get_remote_directory "$flavour" "$slot" "$slot_build_id")" \
        "${ARTIFACTS_DIR}"

    # note that we ignore errors when retrieving the ccache dir
    get_artifact \
        --get-ccache ${platform} \
        $(get_remote_directory $flavour $slot $(( $slot_build_id - 1 )) ) \
        "${ARTIFACTS_DIR}" || true
fi

if [ ! -e "${ARTIFACTS_DIR}/ccache_dir.${slot}.${platform}.tar.bz2" ] ; then
    # if there is no previous ccache dir, we initialize an empty one
    if which ccache &>/dev/null ; then
        mkdir -p ${PWD}/build/.ccache
        env CCACHE_DIR=${PWD}/build/.ccache ccache -M 0 -F 12000
        tar -c -j -f "${ARTIFACTS_DIR}/ccache_dir.${slot}.${platform}.tar.bz2" -C build .ccache
    fi
fi

build_slot \
    "${flavour}" \
    "${slot}" \
    "${slot_build_id}" \
    "${platform}" \
    --build-dir "${ARTIFACTS_DIR}" \
    ${os_label:+--os-label "${os_label}"}
