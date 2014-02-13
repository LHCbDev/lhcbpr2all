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

PERIOD=${1:-3600}

# hack because of a bug with non-writable home (this script is run by tomcat)
export HOME=$PWD

# Set common environment
. $(dirname $0)/common.sh

export CMTCONFIG=$platform

if [ "$JENKINS_MOCK" != "true" -o ! -e configs ] ; then
  # Get the slot configuration files from Subversion
  lbn-get-configs
fi

lbp-check-periodic-tests configs/test_schedule.xml -i $PERIOD -o periodic_tests_list.txt



