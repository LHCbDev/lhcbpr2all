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
'''
LHCb Nightly Build System module.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

# Ensure that we have the contrib directory in the path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'contrib'))
del sys
del os

# Make the Dashboard class visible from the top level for convenience.
from LbNightlyTools.Utils import Dashboard
