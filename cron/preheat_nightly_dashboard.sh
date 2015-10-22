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

page=
ddocurl=
verbose=false

while getopts p:d:hv opt; do
    case $opt in
	p)
          page=$OPTARG
          ;;
	d)
          ddocurl=$OPTARG
          ;;
        v)
          verbose=true
          ;;
        h)
          echo "Usage: $0 [-p <nightly_page>|-d <ddoc_url>]"
          exit 0
          ;;
        ?)
          exit 1
          ;;
    esac
done

if [ -n "$page" ] ; then
    if [ -n "$ddocurl" ] ; then
        echo 'cannot mix -p and -d options'
        exit 1
    fi
else
    page=nightly
fi

if [ -z "$ddocurl" ] ; then
    ddocurl=https://lhcb-nightlies.cern.ch/${page}/_ddoc
    viewbase=https://lhcb-nightlies.cern.ch/${page}/_view
else
    viewbase=${ddocurl}/_view
fi

$verbose && echo "Getting views from ${ddocurl}"

views=$(curl --insecure --silent ${ddocurl} | \
        python -c 'import json, sys; print " ".join(sorted(json.load(sys.stdin).get("views",{})))')

$verbose && echo "  -> ${views}"

for view in ${views} ; do
    $verbose && echo "Triggering view '${view}'."
    curl --insecure --silent --output /dev/null "${viewbase}/${view}?key=0"
done

$verbose && echo done.
