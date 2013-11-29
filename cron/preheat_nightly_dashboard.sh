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

# Run a quick get request on the CouchDB views to trigger the internal caching
#
# example of acron entry:
#  */5 5-16 * * * lxplus.cern.ch $HOME/LbNightlyTools/cron/preheat_nightly_dashboard.sh

for view in projectsNames platformsNames slotsNames diskSpace summaries systemLoad ; do
    url="https://buildlhcb.cern.ch/nightlies/_view/${view}?key=0"
    curl --insecure --silent --output /dev/null "$url"
done
