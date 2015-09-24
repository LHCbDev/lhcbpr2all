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

# Ensure that the dasboard's database contains all the summaries from the
# builds.

# prepare environment
rootdir=$(dirname $0)/..
cd $rootdir

. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh --silent

. setup.sh

python >> $LHCBNIGHTLIES/www/logs/clean_up_reduced_db.log 2>&1 <<EOF
import logging
logging.basicConfig(level=logging.DEBUG)
from LbNightlyTools import Dashboard
from datetime import date, timedelta, datetime
print('%s: removing old data from reduced db' % datetime.now())
# we keep only 14 days
end_date = (date.today() - timedelta(days=15)).isoformat()
d = Dashboard(db_info=('http://buildlhcb.cern.ch:5984', 'nightlies-reduced'))
for day, slot, id in d.slotsByDay(end=end_date):
    print('-> cleaning %s %s %s' % (day, slot, id))
    d.dropBuild(slot, id)
EOF
