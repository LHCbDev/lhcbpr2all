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

# hack because of a bug with non-writable home (this script is run by tomcat)
export HOME=$PWD

# Set common environment
. $(dirname $0)/common.sh

# 5 minutes grace time before getting data from the URL
# see https://its.cern.ch/jira/browse/LBCORE-883
sleep 300

lbn-release-poll --debug http://buildlhcb.cern.ch/cgi-bin/getreleases
