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

. $(dirname $0)/utils.sh

# Set common environment
set_common

# 5 minutes grace time before getting data from the URL
# see https://its.cern.ch/jira/browse/LBCORE-883
sleep 300

lbn-release-poll --debug http://ariadne-lhcb.cern.ch/cgi-bin/getreleases
