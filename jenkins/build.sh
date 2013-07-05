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

# Clean LD_LIBRARY_PATH of /gcc/ entries
# (see comment on issue LBCORE-109 http://cern.ch/go/PLQ7)
export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH | tr : \\n | grep -v /gcc/ | tr \\n :)

# Set common environment
set_config=1
. $(dirname $0)/common.sh

day=$(date +%a)
timestamp=$(date -I)
deploybase=$(dirname /data/${ARTIFACTS_DIR})

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

# hard-coded because it may point to CVMFS
export LHCBNIGHTLIES=/afs/cern.ch/lhcb/software/nightlies

# remove old summaries
rm -rf $LHCBNIGHTLIES/www/logs/${slot}.${day}*

# create old-style progress stamp files
if [ -e $LHCBNIGHTLIES/${slot}/${day} ] ; then
  stamp=$LHCBNIGHTLIES/${slot}/${day}/isStarted-$platform
  date +"%a %b %d %H:%M:%S %Y" > $stamp
  echo ${slot}.${slot_build_id} >> $stamp
  echo ${BUILD_URL} >> $stamp
  echo "https://lemon.cern.ch/lemon-web/index.php?target=process_search&fb=${HOST}" >> $stamp
fi

if [ -e ${ARTIFACTS_DIR}/${slot}.json ] ; then
  config_file=${ARTIFACTS_DIR}/${slot}.json
else
  config_file=${ARTIFACTS_DIR}/configuration.xml#${slot}
fi

# create moving symlinks in the artifacts deployment directory (ASAP)
# (ignore errors, see <https://its.cern.ch/jira/browse/LBCORE-153>)
ssh buildlhcb.cern.ch "mkdir -pv ${deploybase} ; ln -svfT ${slot_build_id} ${deploybase}/${day} ; ln -svfT ${slot_build_id} ${deploybase}/${timestamp}" || true

if [ "${os_label}" = "coverity" ] ; then
  coverity_opt='--coverity'
fi

if [ "$JOB_NAME" = "nightly-slot-build-platform" ] ; then
  deploy_opt="--deploy-reports-to $LHCBNIGHTLIES/www/logs"
else
  deploy_opt="--deploy-reports-to $LHCBNIGHTLIES/www/test/logs"
fi

if [ "$JENKINS_MOCK" != "true" ] ; then
  submit_opt="--submit --cdash-submit"
fi

time lbn-build --verbose --jobs 8 --timeout 18000 --build-id "${slot}.${slot_build_id}.{timestamp}" --artifacts-dir "${ARTIFACTS_DIR}" --rsync-dest "buildlhcb.cern.ch:${deploybase}/${slot_build_id}" --with-tests ${submit_opt} ${deploy_opt} ${coverity_opt} ${config_file}

# if possible generate glimpse indexes and upload them to buildlhcb
if which glimpseindex &> /dev/null ; then
    time lbn-index --verbose --build-id "${slot}.${slot_build_id}.{timestamp}" --artifacts-dir "${ARTIFACTS_DIR}" ${config_file}
    rsync --archive --partial-dir=.rsync-partial.$(hostname).$$ --delay-updates --rsh=ssh "${ARTIFACTS_DIR}/" "buildlhcb.cern.ch:${deploybase}/${slot_build_id}"
fi

if [ -e $LHCBNIGHTLIES/${slot}/${day} ] ; then
  rm -f $stamp
  stamp=$LHCBNIGHTLIES/${slot}/${day}/isDone-$platform
  date +"%a %b %d %H:%M:%S %Y" > $stamp
  echo ${slot}.${slot_build_id} >> $stamp
  echo ${BUILD_URL} >> $stamp
  echo "https://lemon.cern.ch/lemon-web/index.php?target=process_search&fb=${HOST}" >> $stamp
fi

# FIXME: For the special slot lhcb-release we also keep a copy of the
# whole build directory
if [ "${slot}" == "lhcb-release" ] ; then
  tar -c -j -f "${ARTIFACTS_DIR}"/${slot}.${slot_build_id}.${platform}.full.tar.bz2 -C build .
fi
