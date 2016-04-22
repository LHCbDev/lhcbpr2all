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

# Clean up the nightly installation directories on AFS

# prepare environment
rootdir=$(dirname $0)/..
cd $rootdir

. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh --silent

. setup.sh
day=$(date +%a)

# hard-coded because it may point to CVMFS
export LHCBNIGHTLIES=/afs/cern.ch/lhcb/software/nightlies

logfile=$LHCBNIGHTLIES/www/logs/cleanup_slots.log
# clean up the slots
echo "$(date): moving installation areas for $day in trash spaces" >> $logfile 2>&1
cd $LHCBNIGHTLIES
for slotdir in lhcb-*/$day; do
    echo "$(date):      $slotdir" >> $logfile 2>&1
    mkdir -p $slotdir/.trash 2>/dev/null
    mv -f $slotdir/* $slotdir/.installed $slotdir/.lock $slotdir/.trash 2>/dev/null
done
echo "$(date): emptying trashes" >> $logfile 2>&1
rm -rf */$day/.trash > /dev/null 
echo "$(date): done" >> $logfile 2>&1
