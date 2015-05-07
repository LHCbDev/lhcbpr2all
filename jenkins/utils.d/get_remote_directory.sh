export RSYNC_SERVER=${RSYNC_SERVER:-buildlhcb.cern.ch}
export RSYNC_WORKDIR=${RSYNC_WORKDIR:-/data/artifacts}

function get_remote_directory {

    USAGE="get_directory_rsync flavour slot slot_build_id"

    if [ $# != 3 ] ; then
	echo "ERROR : Usage : ${USAGE}"
	exit 1
    fi

    flavour="$1"
    slot="$2"
    slot_build_id="$3"

    RSYNC_DIR="${RSYNC_WORKDIR}/${flavour}/${slot}/${slot_build_id}"
    if [ ! -d "${RSYNC_DIR}" ] ; then
	RSYNC_DIR="${RSYNC_SERVER}:${RSYNC_DIR}"
    fi

    echo "${RSYNC_DIR}"
}
