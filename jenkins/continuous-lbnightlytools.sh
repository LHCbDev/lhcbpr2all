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

# prepare the environment for testing
#. /cvmfs/lhcb.cern.ch/lib/lhcb/LBSCRIPTS/prod/InstallArea/scripts/LbLogin.sh
. /afs/cern.ch/lhcb/software/releases/LBSCRIPTS/dev/InstallArea/scripts/LbLogin.sh --no-cache

. SetupProject.sh LCGCMT 83 Python pytools

set -ex

which python

cd $(dirname $0)/..
. ./setup.sh

(
  # Added the contrib directory to the Python path (needed by pylint)
  export PYTHONPATH=$PWD/python/LbNightlyTools/contrib:$PYTHONPATH
  # Ignoring pylint return code (to avoid failure of the test).
  pylint --rcfile=docs/pylint.rc $( ls python ) > pylint.txt || true
)

nosetests -v --with-doctest --with-xunit --with-coverage --cover-erase --cover-inclusive --cover-package "$(ls -m python)" python
coverage xml --include="python/*"
