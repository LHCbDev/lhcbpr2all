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

# This script is meant as a wrapper around Jenkins scripts so that they can be
# run by hand for testing.
#
# Usage: jenkins/mock.sh <step> <slot> <platform>
#
# where <step> is any of checkout, platforms, preconditions, build
#       <slot> is a slot name
#       <platform> is the platform id string


# Check arguments

if [ $# -lt 3 ] ; then
    echo "Usage: $0 <step> <slot> <platform> [<project>]"
    exit 1
fi

step=$1
slot=$2
platform=$3
project=$4
flavour=${flavour:-mock}

# Prepare Jenkins-like environment
export slot
export platform
export project
export flavour
export NODE_NAME=$(hostname)
# variables that can be overridden
export slot_build_id=${slot_build_id:-999}
export WORKSPACE=${WORKSPACE:-$(cd $(dirname $0)/.. ; pwd)}
export JOB_NAME=${JOB_NAME:-nightly-test-slot-build-platform}
guessed_label=${platform#*-}
guessed_label=${guessed_label%%-*}
export os_label=${os_label:-${guessed_label}}
# this variable might be used inside the Jenkins scripts to avoid some ops
export JENKINS_MOCK=true

command=$WORKSPACE/jenkins/${step}.sh
if [ ! -e $command ] ; then
    echo "invalid step '$step'"
    exit 1
fi

exec $command
