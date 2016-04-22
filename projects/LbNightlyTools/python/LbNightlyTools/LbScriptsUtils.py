###############################################################################
# (c) Copyright 2015 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
'''
Utility functionns to update LbScripts file during the release of the project.

TO BE REMOVED ONCE WE MOVE TO LBENV
'''
__author__ = 'Ben Couturier <ben.couturier@cern.ch>'

import fileinput
import os
import logging
import re
import shutil
import json
from datetime import datetime

def _checkScriptversion(line):
    """
    Find a line matching
    script_version = '151124'
    and return the updated version
    """
    ret = None
    if re.match("^\s*script_version\s*=\s*['\"]\d+['\"]\s*", line):
        ret = "script_version = '%s'\n" % datetime.now().strftime("%y%m%d%H%M%S")
    return ret

def _checkLbScriptsversion(line, version):
    """
    Find a line matching
    lbscripts_version = "v8r3p3"
    and return the updated version
    """
    ret = None
    if re.match("^\s*lbscripts_version\s*=\s*['\"].+['\"]\s*", line):
        ret = 'lbscripts_version = "%s"\n' % version
    return ret


def updateInstallProject(basedir, version):
    '''
    Update version and date in install_project
    '''
    log = logging.getLogger("updateInstallProject")

    # Doing a backup on the original install project 
    ipname = "LbLegacy/python/LbLegacy/install_project.py"
    ipbakname = ipname + ".orig"
    ipfullname = os.path.join(basedir, ipname)
    ipbakfullname = os.path.join(basedir, ipbakname)
    shutil.copy(ipfullname, ipbakfullname)

    # Now mangling the original file
    with open(ipbakfullname, "r") as fin:
        with open(ipfullname, "w") as fout:
            for line in fin:
                ret =  _checkScriptversion(line)
                if ret == None:
                    ret =  _checkLbScriptsversion(line, version)
                if ret != None:
                    fout.write(ret)
                else:
                    fout.write(line)


def _checkReqVersion(line, version):
    """
    Replace occurences of $(version)
    and return the updated version
    """
    ret = None
    m =  re.match("^(.*)\$\(version\)(.*)$", line)
    if m != None:
        ret = "%s%s%s\n" % (m.group(1), version, m.group(2))
    return ret

def updateLbConfigurationRequirements(basedir, version):
    '''
    Update version and date in install_project
    '''
    log = logging.getLogger("updateLbConfReq")

    # Doing a backup on the original install project 
    ipname = "LbConfiguration/cmt/requirements"
    ipbakname = ipname + ".orig"
    ipfullname = os.path.join(basedir, ipname)
    ipbakfullname = os.path.join(basedir, ipbakname)
    shutil.copy(ipfullname, ipbakfullname)

    # Now mangling the original file
    with open(ipbakfullname, "r") as fin:
        with open(ipfullname, "w") as fout:
            for line in fin:
                ret =  _checkReqVersion(line, version)
                if ret != None:
                    fout.write(ret)
                else:
                    fout.write(line)



def  _createVersionCmt(basedir, package, version):
    '''
    Create the version.cmt file in a specific package
    '''
    vfilename = os.path.join(basedir, package, "cmt", "version.cmt") 
    with open(vfilename, "w") as f:
        f.write("%s\n" % version)

def updateVersionCmt(basedir, version):
    '''
    Update version.cmt in all the LbScripts packages
    '''
    log = logging.getLogger("updateVersionCmt")
    packages = ["LbConfiguration",
                "LbLegacy",
                "LbRelease",
                "LbScriptsPolicy",
                "LbScriptsSys",
                "LbUtils"]
    
    for p in packages:
        _createVersionCmt(basedir, p, version)

