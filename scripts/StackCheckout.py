#!/usr/bin/env python
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
import LbUtils.Log
LbUtils.Log._default_log_format = '%(asctime)s:' + LbUtils.Log._default_log_format

from LbNightlyTools.StackCheckout import Script
import sys
sys.exit(Script().run())
