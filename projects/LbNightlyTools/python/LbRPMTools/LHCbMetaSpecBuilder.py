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

tmpdir = TempDir(prefix="LHCbMetaRpmSpec")

__log__ = logging.getLogger(__name__)


#
# Spec for binary RPMs
#
###############################################################################
class LHCbMetaRpmSpec(LHCbBaseRpmSpec):
    """ Class representing a LHCb project"""

    def __init__(self, project, version, requires, buildarea, release=None):
        """ Constructor taking the actual file name """
        super(LHCbMetaRpmSpec, self).__init__(project, version)
        __log__.debug("Creating RPM for %s/%s" % (project, version))

        self._project = project
        self._version = version
        self._lhcb_release_version =  release
        self._buildarea = buildarea
        self._requires = requires
        self._arch = "noarch"
        
    def getRPMName(self, norelease=False):
        ''' Return the architecture, always noarch for our packages'''
        if norelease:
            return  "-".join([self._project, self._version])
        full = "-".join([self._project, self._version, str(self._lhcb_release_version)])
        final = ".".join([full, self._arch, "rpm"])
        return final
                             
    def _createHeader(self):
        '''
        Prepare the RPM header
        '''
        header = Template("""
%define buildarea ${buildarea}
%define project ${project}
%define version ${version}
%define release ${release}
%define arch    ${arch}

%global __os_install_post /usr/lib/rpm/check-buildroot

%define _topdir %{buildarea}/rpmbuild
%define tmpdir %{buildarea}/tmpbuild
%define _tmppath %{buildarea}/tmp

Name: %{project}
Version: %{version}
Release: ${release}
Vendor: LHCb
Summary: %{project}
License: GPL
Group: LHCb
BuildRoot: %{tmpdir}/%{name}-buildroot
BuildArch: %{arch}
AutoReqProv: no
Prefix: /opt/LHCbSoft
Provides: /bin/sh
Provides: %{project} = %{version}

\n""").substitute(buildarea = self._buildarea,
                  project = self._project,
                  version = self._version,
                  release = self._lhcb_release_version,
                  arch = self._arch
                  )
        return header

    def _createRequires(self):
        '''
        Prepare the Requires section of the RPM
        '''
        tmp = ""
        for r in self._requires:

            tmp +=  "Requires: %s\n" % r
                                 
        return tmp

    def _createDescription(self):
        '''
        Prepare the Requires section of the RPM
        '''
        tmp  = "%description\n"
        tmp += "%{project}\n\n"
        return tmp

    def _createInstall(self):
        '''
        Prepare the Install section of the RPM
        '''
        spec = "%install\n"
        spec += "\n\n"
        return spec

    def _createTrailer(self):
        '''
        Prepare the RPM header
        '''
        trailer = Template("""
%files

%post

%postun

%clean

%define date    %(echo `LC_ALL=\"C\" date +\"%a %b %d %Y\"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version
""").substitute(buildarea = self._buildarea)

        return trailer

#
# Main Script to generate the spec file
#
###############################################################################
import LbUtils.Script
class MetaScript(LbUtils.Script.PlainScript):
    '''
    Script to generate the Spec file for an LHCb project.
    '''
    __usage__ = '''%prog [options] rpmname rpmversion requirement1 requirement2 [...]

e.g. %prog -o tmp.spec OnlineFarmMeta 1.0.0 MOOREONLINE_v23r4_x86_64_slc6_gcc48_opt ALIGNMENTONLINE_v10r2_x86_64_slc6_gcc48_opt'''
    __version__ = ''

    def addBasicOptions(self, parser):
        '''
        Add some basic (common) options to the option parser
        '''
        parser.add_option('-v', '--version',
                          dest="version",
                          default=None,
                          action="store",
                          help="Force LCG version")
        parser.add_option('-p', '--platform',
                          dest="platform",
                          default=None,
                          action="store",
                          help="Force platform")
        parser.add_option('-n', '--name',
                          dest="name",
                          default=None,
                          action="store",
                          help="Force the name of the RPM generated")
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
        parser.add_option('-t', '--fromtag',
                          dest="tag",
                          default = None,
                          action="store",
                          help="Take the project versions tagged as specified in the conf DB (instead of command line)")
 
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
        if len(self.args) < 2:
            self.parser.error('wrong number of arguments')

        # Extracting info from filename
        project = self.args[0]
        version = self.args[1]

        if  self.options.tag:
            try:
                from LbRelease.SoftConfDB.SoftConfDB import SoftConfDB
                db = SoftConfDB()
                projects = db.listTag(self.options.tag.upper())
                requires = []
                for (p,v,f) in projects:
                    requires.append("_".join([p.upper(), v, f.replace("-", "_")]))
            except:
                print "Could not access SoftConfDB, exiting"
                return 2
        else:
            requires = self.args[2:]

        self.log.warning("Generating Meta RPM for %s %s" % (project, version))

        buildarea = self.options.buildarea
        self.createBuildDirs(buildarea, project + "_" +  version)

        specname = project
        if self.options.name != None:
            specname = self.options.name
        spec = LHCbMetaRpmSpec(specname, version, requires,  buildarea)

        if self.options.output:
            with open(self.options.output, "w") as outputfile:
                outputfile.write(spec.getSpec())
        else:
            print spec.getSpec()

