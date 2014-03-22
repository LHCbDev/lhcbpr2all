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

if [ $(python -c 'import sys; print "%d%d" % sys.version_info[:2]') = 24 ] ; then 
  # FIXME: On SLC5 the default Python is the system one (with LCG 68)
  . SetupProject.sh LCGCMT 66 Python pytools
else
  . SetupProject.sh LCGCMT Python pytools
fi 

set -ex

which python

cd $(dirname $0)/..
. ./setup.sh

nosetests -v --with-doctest --with-xunit --with-coverage --cover-erase --cover-inclusive --cover-package LbNightlyTools python
coverage xml --include="python/*"

# Added the contrib directory to the Python path (needed by pylint)
export PYTHONPATH=$PWD/python/LbNightlyTools/contrib:$PYTHONPATH
# Ignoring pylint return code (to avoid failure of the test).
pylint --rcfile=docs/pylint.rc LbNightlyTools > pylint.txt || true
