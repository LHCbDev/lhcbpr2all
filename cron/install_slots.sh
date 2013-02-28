#!/bin/bash
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
    InstallSlot.py $slot $day >> $logfile 2>&1
done
