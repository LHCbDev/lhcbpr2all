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

# Record disk usage in the dasboard.

# prepare environment
rootdir=$(dirname $0)/..
cd $rootdir

. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh --silent

. setup.sh
day=$(date +%a)

# hard-coded because it may point to CVMFS
export LHCBNIGHTLIES=/afs/cern.ch/lhcb/software/nightlies

# get the list of slots
slots_on_afs=$(svn cat svn+ssh://svn.cern.ch/reps/lhcb/LHCbNightlyConf/trunk/slots_on_afs.txt | grep -v '^ *#')
#slots_on_afs=$(cat slots_on_afs.txt | grep -v '^ *#')

logfile=$LHCBNIGHTLIES/www/logs/monitor_disk_usage.log
# install the slots
echo "$(date): checking disk usage ($day)" >> $logfile 2>&1
cd $LHCBNIGHTLIES
for slot in $slots_on_afs ; do
    lbn-monitor-disk --slot $slot --build-id $day $slot/$day >> $logfile 2>&1
done
