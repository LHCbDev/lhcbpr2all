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

export RSYNC_SERVER=${RSYNC_SERVER:-buildlhcb.cern.ch}
export RSYNC_WORKDIR=${RSYNC_WORKDIR:-/data/artifacts}

function get_remote_directory {

    local USAGE="get_directory_rsync flavour slot slot_build_id"

    if [ $# != 3 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    local flavour="$1"
    local slot="$2"
    local slot_build_id="$3"

    local RSYNC_DIR="${RSYNC_WORKDIR}/${flavour}/${slot}/${slot_build_id}"
    if [ ! -d "${RSYNC_DIR}" ] ; then
	local RSYNC_DIR="${RSYNC_SERVER}:${RSYNC_DIR}"
    fi

    echo "${RSYNC_DIR}"
}

function create_alias {

    local day=$(date +%a)
    local timestamp=$(date -I)
    local RSYNC_DIR="${RSYNC_WORKDIR}/${flavour}/${slot}"

    local COMMAND="mkdir -pv ${RSYNC_DIR} ; ln -svfT ${slot_build_id} ${RSYNC_DIR}/${day} ; ln -svfT ${slot_build_id} ${RSYNC_DIR}/${timestamp}"

    if [ ! -d "${RSYNC_WORKDIR}" ] ; then
	local COMMAND="ssh ${RSYNC_SERVER} ${COMMAND} || true"
    fi

    ${COMMAND}
}