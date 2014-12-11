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

# Install required nightly build slots on AFS

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

logfile=$LHCBNIGHTLIES/www/logs/install_slots.log
# install the slots
echo "$(date): installing slots for $day" >> $logfile 2>&1
cd $LHCBNIGHTLIES
for slot in $slots_on_afs ; do
    echo "$(date):   - $slot" >> $logfile 2>&1
    lbn-install $slot $day >> $logfile 2>&1
    # ensure that the symlink 'Today' points to the right day
    if [ $(readlink $slot/Today) != "$day" ] ; then
        ln -sfTv $day $slot/Today >> $logfile 2>&1
    fi
done


