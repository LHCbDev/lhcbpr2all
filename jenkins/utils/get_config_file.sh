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

if [ "$SET_COMMON" != "true" ] ; then
    echo "ERROR : $0 need SET_COMMON set with true"
    exit 1
fi

lbn-manage-rsync --verbose --get-config --source "${RSYNC_DIR}" --destination "${ARTIFACTS_DIR}"

if [ -e ${ARTIFACTS_DIR}/${slot}.json ] ; then
	export config_file=${ARTIFACTS_DIR}/${slot}.json
else
	export config_file=${ARTIFACTS_DIR}/configuration.xml#${slot}
fi

export GET_CONFIG_FILE="true"