"""
Utility module, with various utility functions
"""

import os
import re

# Util method to prepare the build area
################################################################################
def checkBuildArea(ba):

    if not os.path.exists(ba):
        os.makedirs(ba)

    basdirs = [ 'rpmbuild', 'tmpbuild', 'tmp' ]
    for s in basdirs:
        tmp = os.path.join(ba, s)
        if not os.path.exists(tmp):
            os.makedirs(tmp)

    rpmbuild =  os.path.join(ba, 'rpmbuild')
    sdirs = [ 'SOURCES', 'RPMS', 'BUILD', 'SRPMS' ]
    for s in sdirs:
        tmp = os.path.join(rpmbuild, s)
        if not os.path.exists(tmp):
            os.makedirs(tmp)

# Check if the version matches the LHCb standard
################################################################################

def checkVersion(version):

    m = re.match("v([\d]+)r([\d]+)$", version)
    if m != None:
        return True
    else:
        # Checking whetehr the version matches vXrYpZ in that case
        m = re.match("v([\d]+)r([\d]+)p([\d]+)$", version)
        if m != None:
            return True
        else:
            return False



# Parsing version
################################################################################
def parseVersion(version):
    maj_version = 1
    min_version = 0
    patch_version = 0

    m = re.match("v([\d]+)r([\d]+)$", version)
    if m != None:
        maj_version = m.group(1)
        min_version = m.group(2)
    else:
        # Checking whether the version matches vXrYpZ in that case
        m = re.match("v([\d]+)r([\d]+)p([\d]+)", version)
        if m != None:
            maj_version = m.group(1)
            min_version = m.group(2)
            patch_version = m.group(3)
        else:
            raise Exception("Version %s does not match format vXrY or vXrYpZ" % version)

    return (maj_version, min_version, patch_version)
