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
Class to generate RPM Spec for metadapackages that require all the needed packages from
externals.

Created on Feb 27, 2014

@author: Ben Couturier
'''

import os
import re
import sys
import logging
from string import Template
from subprocess import Popen, PIPE

from LHCbRPMSpecBuilder import LHCbBaseRpmSpec
from LbLegacy.Utils import getStatusOutput
from LbUtils.Temporary import TempDir
from LbUtils.CMT.Common import CMTCommand as CMT

tmpdir = TempDir(prefix="LHCbLbScriptsRpmSpec")
PREFIX="/opt/LHCbSoft"

__log__ = logging.getLogger(__name__)

def parseVersion(version):
    '''
    Parse the version string
    '''
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
# Spec for binary RPMs
#
###############################################################################
class LHCbLbScriptsRpmSpec(LHCbBaseRpmSpec):
    """ Class representing a LHCb project"""

    def __init__(self, project, version, buildarea, releasedir):
        """ Constructor taking the actual file name """
        super(LHCbLbScriptsRpmSpec, self).__init__(project, version)
        __log__.debug("Creating RPM for %s/%s" % (project, version))
        self._project = project
        self._version = version
        self._buildarea = buildarea
        (self._lhcb_maj_version,
         self._lhcb_min_version,
         self._lhcb_patch_version) = (1, 0, 0)
        self._lhcb_release_version = 0
        self._releasedir = releasedir
        
    def getRPMName(self, norelease=False):
        ''' Return the architecture, always noarch for our packages'''
        projname =  "_".join([self._project.upper(),
                              self._version])
        projver = ".".join([str(n) for n in [ self._lhcb_maj_version,
                                              self._lhcb_min_version,
                                              self._lhcb_patch_version]])
        if norelease:
            return "-".join([projname, projver])
        full = "-".join([projname, projver, str(self._lhcb_release_version)])
        final = ".".join([full, self._arch, "rpm"])
        return final

    def _createHeader(self):
        '''
        Prepare the RPM header
        '''
        header = Template("""
%define lhcb_maj_version ${lhcb_maj_version}
%define lhcb_min_version ${lhcb_min_version}
%define lhcb_patch_version ${lhcb_patch_version}
%define lhcb_release_version ${lhcb_release_version}
%define buildarea ${buildarea}
%define project ${project}
%define projectUp ${projectUp}
%define lbversion ${version}
%define _postshell /bin/bash
%define prefix ${prefix}
%define releasedir ${releasedir}

%global __os_install_post /usr/lib/rpm/check-buildroot

%define _topdir %{buildarea}/rpmbuild
%define tmpdir %{buildarea}/tmpbuild
%define _tmppath %{buildarea}/tmp

Name: %{projectUp}_%{lbversion}
Version: %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Release: %{lhcb_release_version}
Vendor: LHCb
Summary: %{project}
License: GPL
Group: LHCb
BuildRoot: %{tmpdir}/%{name}-buildroot
BuildArch: noarch
AutoReqProv: no
Prefix: %{prefix}
Provides: /bin/sh
Provides: /bin/bash

Requires(post): CMT
Requires: COMPAT

        \n""").substitute(buildarea = self._buildarea,
                          project = self._project,
                          projectUp = self._project.upper(),
                          version = self._version,
                          lhcb_maj_version = self._lhcb_maj_version,
                          lhcb_min_version = self._lhcb_min_version,
                          lhcb_patch_version = self._lhcb_patch_version,
                          lhcb_release_version = self._lhcb_release_version,
                          prefix = PREFIX,
                          releasedir = self._releasedir
                          )

        return header


    def _createRequires(self):
        '''
        Prepare the Requires section of the RPM
        '''
        return ""
    
    def _createDescription(self):
        '''
        Prepare the Requires section of the RPM
        '''
        tmp  = "%description\n"
        tmp += "%{project} %{lbversion}\n\n"
        return tmp

    def _createInstall(self):
        '''
        Prepare the Install section of the RPM
        '''
        spec = "%install\n"
        spec += '''

[ -d ${RPM_BUILD_ROOT} ] && rm -rf ${RPM_BUILD_ROOT}

mkdir -p ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}

if [ $? -ne 0 ]; then
  exit $?
fi

rsync -avrz %{releasedir}/%{projectUp}/%{projectUp}_%{lbversion}/* ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}

if [ $? -ne 0 ]; then
  exit $?
fi


        '''
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

if [ -f $PREFIX/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/%{project}Sys/cmt/Update.py ]; then
echo "Creating link in update.d"
mkdir -p -v $PREFIX/etc/update.d
ln -s $PREFIX/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/%{project}Sys/cmt/Update.py $PREFIX/etc/update.d/%{package}_Update.py
echo "Running Update script"
. $PREFIX/LbLogin.sh --silent --mysiteroot=$PREFIX
echo "Now using python:"
which python
echo "PYTHONPATH: $PYTHONPATH"
echo "PATH: $PATH"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
python $PREFIX/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/%{project}Sys/cmt/Update.py
fi

if [ -f $PREFIX/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/%{project}Sys/cmt/PostInstall.py ]; then
echo "Running PostInstall script"
python $PREFIX/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/%{project}Sys/cmt/PostInstall.py
fi

%postun -p /bin/bash

%files
%defattr(-,root,root)
%{prefix}/lhcb/%{projectUp}/%{projectUp}_%{lbversion}


%define date    %(echo `LC_ALL=\"C\" date +\"%a %b %d %Y\"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version

        '''

        return trailer


#
# Spec for the LHCb holder package
#
###############################################################################
class LHCbLbScriptsLinkRpmSpec(LHCbBaseRpmSpec):
    """ Class representing a LHCb project"""

    def __init__(self, project, version, linkname, rpmname, buildarea, releasedir):
        """ Constructor taking the actual file name """
        super(LHCbLbScriptsLinkRpmSpec, self).__init__(project, version)
        __log__.debug("Creating RPM for %s/%s" % (project, version))
        self._project = project
        self._version = version
        self._buildarea = buildarea
        self._linkname = linkname
        (self._lhcb_maj_version,
         self._lhcb_min_version,
         self._lhcb_patch_version) = parseVersion(version)
        self._lhcb_release_version = 0
        self._releasedir = releasedir
        self._rpmname = rpmname
        
    def getRPMName(self, norelease=False):
        ''' Return the architecture, always noarch for our packages'''
        projname =  self._rpmname
        projver = ".".join([str(n) for n in [ self._lhcb_maj_version,
                                              self._lhcb_min_version,
                                              self._lhcb_patch_version]])
        if norelease:
            return "-".join([projname, projver])
        full = "-".join([projname, projver, str(self._lhcb_release_version)])
        final = ".".join([full, self._arch, "rpm"])
        return final

    def _createHeader(self):
        '''
        Prepare the RPM header
        '''
        header = Template("""
%define lhcb_maj_version ${lhcb_maj_version}
%define lhcb_min_version ${lhcb_min_version}
%define lhcb_patch_version ${lhcb_patch_version}
%define lhcb_release_version ${lhcb_release_version}
%define buildarea ${buildarea}
%define project ${project}
%define projectUp ${projectUp}
%define lbversion ${version}
%define _postshell /bin/bash
%define prefix ${prefix}
%define releasedir ${releasedir}
%define linkname ${linkname}
%define rpmname ${rpmname}

%global __os_install_post /usr/lib/rpm/check-buildroot

%define _topdir %{buildarea}/rpmbuild
%define tmpdir %{buildarea}/tmpbuild
%define _tmppath %{buildarea}/tmp

Name: %{rpmname}
Version: %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Release: %{lhcb_release_version}
Vendor: LHCb
Summary: %{project}
License: GPL
Group: LHCb
BuildRoot: %{tmpdir}/%{name}-buildroot
BuildArch: noarch
AutoReqProv: no
Prefix: %{prefix}
Provides: /bin/sh
Provides: /bin/bash

Requires:  %{projectUp}_%{lbversion}

        \n""").substitute(buildarea = self._buildarea,
                          project = self._project,
                          projectUp = self._project.upper(),
                          version = self._version,
                          lhcb_maj_version = self._lhcb_maj_version,
                          lhcb_min_version = self._lhcb_min_version,
                          lhcb_patch_version = self._lhcb_patch_version,
                          lhcb_release_version = self._lhcb_release_version,
                          prefix = PREFIX,
                          releasedir = self._releasedir,
                          linkname = self._linkname,
                          rpmname = self._rpmname
                          )

        return header


    def _createRequires(self):
        '''
        Prepare the Requires section of the RPM
        '''
        return ""
    
    def _createDescription(self):
        '''
        Prepare the Requires section of the RPM
        '''
        tmp  = "%description\n"
        tmp += "%{project} %{lbversion}\n\n"
        return tmp

    def _createInstall(self):
        '''
        Prepare the Install section of the RPM
        '''
        spec = "%install\n"
        spec += '''

[ -d ${RPM_BUILD_ROOT} ] && rm -rf ${RPM_BUILD_ROOT}

mkdir -p ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}
cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}
ln -s %{projectUp}_%{lbversion} %{linkname}

        '''
        return spec

    def _createTrailer(self):
        '''
        Prepare the RPM header
        '''
        trailer = '''
%clean

%post

%postun

%files
%defattr(-,root,root)
%{prefix}/lhcb/%{projectUp}/%{linkname}


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
    __usage__ = '''%prog [options] project version platform

e.g. %prog LHCbExternals v68r0 x86_64-slc6-gcc48-opt'''
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
        parser.add_option('-e', '--releasedir',
                          dest="releasedir",
                          default=os.environ["LHCBRELEASES"],
                          action="store",
                          help="LHCb Releases area")
        parser.add_option('--prod',
                          dest="buildprodrpm",
                          default=False,
                          action="store_true",
                          help="Build package with links")
        parser.add_option('--dev',
                          dest="builddevrpm",
                          default=False,
                          action="store_true",
                          help="Build package with links for dev")

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
            self.parser.error('wrong number of arguments')

        # Extracting info from filename
        project = "LbScripts"
        version = self.args[0]

        self.log.warning("Packaging LbScripts %s" % version)

        buildarea = self.options.buildarea
        self.createBuildDirs(buildarea, project + "_" +  version)
        releasedir = self.options.releasedir

        if self.options.buildprodrpm:
            spec = LHCbLbScriptsLinkRpmSpec(project, version, "prod", "LBSCRIPTS",
                                            buildarea, releasedir)
        elif self.options.builddevrpm:
            spec = LHCbLbScriptsLinkRpmSpec(project, version, "dev", "LBSCRIPTSDEV",
                                        buildarea, releasedir)
        else:
            spec = LHCbLbScriptsRpmSpec(project, version,
                                        buildarea, releasedir)
            

        if self.options.output:
            with open(self.options.output, "w") as outputfile:
                outputfile.write(spec.getSpec())
        else:
            print spec.getSpec()

