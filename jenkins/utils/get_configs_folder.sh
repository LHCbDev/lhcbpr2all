#!/bin/sh
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

# simple wrapper script to check out the current nightly slots configurations

if [ "$JENKINS_MOCK" != "true" -o ! -e configs ] ; then
  # Get the slot configuration files from Subversion
  lbn-get-configs
fi

export GET_CONFIGS_FOLDER=true