###############################################################################
# (c) Copyright 2014 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
'''
Class to generate the spec file for

Created on Feb 27, 2014

@author: Ben Couturier
'''

import os
import re
import logging
from string import Template
from subprocess import Popen, PIPE

from LHCbRPMSpecBuilder import LHCbBaseRpmSpec
from LbLegacy.Utils import getStatusOutput
from LbUtils.Temporary import TempDir
from LbUtils.CMT.Common import CMTCommand as CMT

tmpdir = TempDir(prefix="LHCbDatapkgRpmSpec")

__log__ = logging.getLogger(__name__)


#
# Utility functions
#
###############################################################################
def parsePackageBuildDirName(builddir):
    """ Split the build directory to extract project name """
    # First making sure we have a normalized path
    rpath = os.path.realpath(builddir)

    # Getting the 2 levels above
    (tmp, version) = os.path.split(rpath)
    (tmp, package) = os.path.split(tmp)
    hat = None
    (prefix, project) = os.path.split(tmp)
    if project not in ['DBASE', 'PARAM']:
        hat = project
        (prefix, project) = os.path.split(prefix)

    return (prefix, project, hat, package, version)

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

#
# Spec for data package RPM
#
###############################################################################
class LHCbDataPackageRpmSpec(LHCbBaseRpmSpec):
    """ Class representing the spec file for a LHCb data package"""

    def __init__(self, releasedir, project, hat, package, version, buildarea, buildlocation, release =1):
        """ Constructor taking the actual file name """
        super(LHCbDataPackageRpmSpec, self).__init__(project, version)
        __log__.debug("Creating RPM for %s/%s" % (package, version))
        self._releasedir = releasedir
        self._project = project
        self._hat = hat
        self._package = package
        self._version = version
        self._buildarea = buildarea
        self._buildlocation = buildlocation
        self._release = release
        (self._majver, self._minver, self._patchver) = parseVersion(version)
        if hat != None:
            self._fullname = "_".join([self._project.upper(), self._hat,  self._package])
            self._versiondir = os.path.join(self._project.upper(), self._hat,  self._package)
        else:
            self._fullname = "_".join([self._project.upper(),  self._package])
            self._versiondir = os.path.join(self._project.upper(), self._package)
        
    def _createHeader(self):
        '''
        Prepare the RPM header
        '''
        header = Template("""
%define prefix /opt/LHCbSoft
%define majver ${majver}
%define minver ${minver}
%define patchver ${patchver}
%define buildarea ${buildarea}
%define project ${project}
%define projectUp ${projectUp}
%define hat ${hat}
%define package ${package}
%define lbversion ${lbversion}
%define fullname ${fullname}
%define release ${release}
%define versiondir ${versiondir}
%define releasedir ${releasedir}
%global __os_install_post /usr/lib/rpm/check-buildroot

%define _topdir %{buildarea}/rpmbuild
%define tmpdir %{buildarea}/tmpbuild
%define _tmppath %{buildarea}/tmp


%define _postshell /bin/bash

Name: %{fullname}
Version: %{majver}.%{minver}.%{patchver}
Release: %{release}
Vendor: LHCb
Summary: %{fullname}
License: GPL
Group: LHCb
BuildRoot: %{tmpdir}/%{name}-buildroot
BuildArch: noarch
AutoReqProv: no
Prefix: %{prefix}
Provides: /bin/sh
Provides: /bin/bash
Provides: %{package} = %{majver}.%{minver}.%{patchver}
Provides: %{fullname} = %{majver}.%{minver}.%{patchver}
Provides: %{package}_v%{majver} = %{majver}.%{minver}.%{patchver}
Provides: %{fullname}_v%{majver} =  %{majver}.%{minver}.%{patchver}
Requires: %{projectUp}_common
Requires(post): LBSCRIPTS
Requires(post): COMPAT



        \n""").substitute(majver = self._majver, minver = self._minver, patchver = self._patchver,
                          buildarea = self._buildarea,
                          project = self._project, projectUp = self._project.upper(),
                          package = self._package, lbversion = self._version, hat = self._hat,
                          fullname = self._fullname, release = self._release,
                          versiondir = self._versiondir, releasedir = self._releasedir)

        return header

    def _createRequires(self):
        '''
        Prepare the Requires section of the RPM
        '''
        tmp = ""        
        return tmp

    def _createDescription(self):
        '''
        Prepare the Requires section of the RPM
        '''
        tmp  = "%description\n"
        tmp += "%{fullname} %{version}\n\n"
        return tmp

    def _createInstall(self):
        '''
        Prepare the Install section of the RPM
        '''
        spec = '''%install
        
[ -d ${RPM_BUILD_ROOT} ] && rm -rf ${RPM_BUILD_ROOT}

/bin/mkdir -p ${RPM_BUILD_ROOT}%{prefix}/lhcb/%{versiondir}
if [ $? -ne 0 ]; then
  exit $?
fi

cp -r %{releasedir} ${RPM_BUILD_ROOT}%{prefix}/lhcb/%{versiondir}
if [ $? -ne 0 ]; then
  exit $?
fi'''

        
        spec += "\n\n"
        return spec

    def _createTrailer(self):
        '''
        Prepare the RPM header
        '''
        trailer = '''

%clean

%post -p /bin/bash

if [ "$MYSITEROOT" ]; then
PREFIX=$MYSITEROOT
else
PREFIX=%{prefix}
fi

if [ -f $PREFIX/etc/update.d/%{package}_Update.py ]; then
rm -f $PREFIX/etc/update.d/%{package}_Update.py
fi

if [ -f $PREFIX/lhcb/%{versiondir}/%{lbversion}/cmt/Update.py ]; then
echo "Creating link in update.d"
mkdir -p -v $PREFIX/etc/update.d
ln -s $PREFIX/lhcb/%{versiondir}/%{lbversion}/cmt/Update.py $PREFIX/etc/update.d/%{package}_Update.py
echo "Running Update script"
. $PREFIX/LbLogin.sh --silent --mysiteroot=$PREFIX
echo "Now using python:"
which python
echo "PYTHONPATH: $PYTHONPATH"
echo "PATH: $PATH"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
python $PREFIX/lhcb/%{versiondir}/%{lbversion}/cmt/Update.py
fi

if [ -f $PREFIX/lhcb/%{versiondir}/%{lbversion}/cmt/PostInstall.py ]; then
echo "Running PostInstall script"
. $PREFIX/LbLogin.sh --silent --mysiteroot=$PREFIX
python $PREFIX/lhcb/%{versiondir}/%{lbversion}/cmt/PostInstall.py
fi

%postun -p /bin/bash
if [ "$MYSITEROOT" ]; then
PREFIX=$MYSITEROOT
else
PREFIX=%{prefix}
fi
echo "In uninstall script"
if [ -h $PREFIX/etc/update.d/%{package}_Update.py ]; then
echo "Removing link to update script:  $PREFIX/etc/update.d/%{package}_Update.py"
rm $PREFIX/etc/update.d/%{package}_Update.py
fi

%files
%defattr(-,root,root)
%{prefix}/lhcb/%{versiondir}/%{lbversion}


%define date    %(echo `LC_ALL=\"C\" date +\"%a %b %d %Y\"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version

        '''

        return trailer

#
# Main Script to generate the spec file
#
###############################################################################
import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Script to generate the Spec file for an LHCb project.
    '''
    __usage__ = '''%prog [options] package version

e.g. %prog DecFiles v25r12'''
    __version__ = ''

    def addBasicOptions(self, parser):
        '''
        Add some basic (common) options to the option parser
        '''
        parser.add_option('-b', '--buildarea',
                          dest="buildarea",
                          default="/tmp",
                          action="store",
                          help="Force build root")
        parser.add_option('-o', '--output',
                          dest="output",
                          default = None,
                          action="store",
                          help="File name for the generated specfile [default output to stdout]")
        return parser

    def defineOpts(self):
        '''
        Prepare the option parser.
        '''
        self.addBasicOptions(self.parser)

    def createBuildDirs(self, buildarea, buildname):
        '''
        Create directories necessary to the build
        '''
        self.topdir = "%s/rpmbuild" % buildarea
        self.tmpdir = "%s/tmpbuild" % buildarea
        self.rpmtmp = "%s/tmp" % buildarea
        self.srcdir = os.path.join(self.topdir, "SOURCES")
        self.rpmsdir =  os.path.join(self.topdir, "RPMS")
        self.srpmsdir =  os.path.join(self.topdir, "SRPMS")
        self.builddir =  os.path.join(self.topdir, "BUILD")

        # And creating them if needed
        for d in [self.rpmtmp, self.srcdir, self.rpmsdir, self.srpmsdir, self.builddir]:
            if not os.path.exists(d):
                os.makedirs(d)

        self.buildroot = os.path.join(self.tmpdir, "%s-buildroot" % buildname)

        if not os.path.exists(self.buildroot):
            os.makedirs(self.buildroot)

    def main(self):
        '''
        Main method for the script
        '''
        if len(self.args) != 1:
            self.parser.error('Please specify package build directory')

        buildlocation = self.args[0]
        (prefix, project, hat, package, version) = parsePackageBuildDirName(buildlocation)
        self.log.warning("Processing data package %s %s" % (package, version))

        buildarea = self.options.buildarea
        self.createBuildDirs(buildarea, package + "_" +  version)

        spec = LHCbDataPackageRpmSpec(buildlocation, project, hat, package, version, buildarea, buildlocation)

        if self.options.output:
            with open(self.options.output, "w") as outputfile:
                outputfile.write(spec.getSpec())
        else:
            print spec.getSpec()

