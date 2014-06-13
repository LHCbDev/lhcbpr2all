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
Class to generate RPM Specfile

Created on Feb 27, 2014

@author: Ben Couturier
'''

import os
import re
import logging
from string import Template

__log__ = logging.getLogger(__name__)

class RpmDirConfig:
    ''' Placeholder for directory config '''
    def __init__(self, buildarea, buildname):
        self.buildarea = buildarea
        self.buildname = buildname
        
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

    def removeBuildArea(self):
        ''' Clean up the dirs '''
        import shutil
        if os.path.exists(self.buildarea):
            shutil.rmtree(self.buildarea)


#
# Base class for spec files
#
###############################################################################
class LHCbBaseRpmSpec(object):
    """ Class representing a LHCb project"""
    def __init__(self, project, version):
        self._project = project
        self._version = version

    def getSpec(self):
        """ Build the global spec file """
        return str(self._createHeader()) \
               + str(self._createRequires()) \
               + str(self._createDescription()) \
               + str(self._createInstall()) \
               + str(self._createTrailer())

    def _createHEPToolsRequires(self):
        """ Creates the depedency on the HepTools (LHCbExternals) RPM """
        (hver, hcmtconfig, hsystem) = self._manifest.getHEPTools()
        return "Requires: LHCbExternals_%s_%s\n"  % (hver, hcmtconfig.replace("-", "_"))
        

#
# Spec for shared RPMs
#
###############################################################################
class LHCbSharedRpmSpec(LHCbBaseRpmSpec):
    """ Class representing the Spec file for an RPM containing the shared files for the project """

    def __init__(self, project, version, sharedTar, buildarea, buildlocation, manifest):
        """ Constructor  """
        super(LHCbSharedRpmSpec, self).__init__(project, version)
        __log__.debug("Creating Shared RPM for %s/%s" % (project, version))
        self._project = project
        self._version = version
        self._sharedTar = sharedTar
        self._buildarea = buildarea
        self._buildlocation = buildlocation
        self._manifest = manifest

    def _createHeader(self):
        '''
        Prepare the RPM header
        '''
        header = Template("""
%define lhcb_maj_version 1
%define lhcb_min_version 0
%define lhcb_patch_version 0
%define buildarea ${buildarea}
%define buildlocation ${buildlocation}
%define project ${project}
%define projectUp ${projectUp}
%define lbversion ${version}

%global __os_install_post /usr/lib/rpm/check-buildroot

%define _topdir %{buildarea}/rpmbuild
%define tmpdir %{buildarea}/tmpbuild
%define _tmppath %{buildarea}/tmp

Name: %{projectUp}_%{lbversion}
Version: %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Release: 1
Vendor: LHCb
Summary: %{project}
License: GPL
Group: LHCb
BuildRoot: %{tmpdir}/%{name}-buildroot
BuildArch: noarch
AutoReqProv: no
Prefix: /opt/LHCbSoft
Provides: /bin/sh
Provides: %{projectUp}_%{lbversion} = %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}

        \n""").substitute(buildarea = self._buildarea,
                          buildlocation = self._buildlocation,
                          project = self._project,
                          projectUp = self._project.upper(),
                          version = self._version)

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
        tmp += "%{project}\n\n"
        return tmp

    def _createInstall(self):
        '''
        Prepare the Install section of the RPM
        '''
        spec = "%install\n"
        spec += "mkdir -p ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}\n"
        if self._sharedTar != None:
            #spec += "cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion} && tar zxf %s" % self._sharedTar
            spec += "cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb && tar zxf %s" % self._sharedTar
        else:
            spec += "cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb && getpack --no-eclipse-config --no-config -P -r % s %s" % (self._project, self._version)

        spec += "\n\n"
        return spec

    def _createTrailer(self):
        '''
        Prepare the RPM header
        '''
        trailer = Template("""
%post

%postun

%clean

%files
%defattr(-,root,root)
/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}

%define date    %(echo `LC_ALL=\"C\" date +\"%a %b %d %Y\"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version
""").substitute(buildarea = self._buildarea,
                        project = self._project,
                        projectUp = self._project.upper(),
                        version = self._version)


        return trailer

#
# Spec for binary RPMs
#
###############################################################################
class LHCbBinaryRpmSpec(LHCbBaseRpmSpec):
    """ Class representing a LHCb project"""

    def __init__(self, project, version, cmtconfig, buildarea, buildlocation, manifest):
        """ Constructor taking the actual file name """
        super(LHCbBinaryRpmSpec, self).__init__(project, version)
        __log__.debug("Creating RPM for %s/%s/%s" % (project, version, cmtconfig))
        self._project = project
        self._version = version
        self._cmtconfig = cmtconfig
        self._buildarea = buildarea
        self._buildlocation = buildlocation
        self._manifest = manifest
        self._lhcb_maj_version = 1
        self._lhcb_min_version = 0
        self._lhcb_patch_version = 0
        self._lhcb_release_version = 1
        self._arch = "noarch"

    def getArch(self):
        ''' Return the architecture, always noarch for our packages'''
        return self._arch

    def getRPMName(self):
        ''' Return the architecture, always noarch for our packages'''
        projname =  "_".join([self._project.upper(),
                              self._version,
                              self._cmtconfig.replace('-', '_')])
        projver = ".".join([str(n) for n in [ self._lhcb_maj_version,
                                              self._lhcb_min_version,
                                              self._lhcb_patch_version]])
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
%define buildlocation ${buildlocation}
%define project ${project}
%define projectUp ${projectUp}
%define cmtconfig ${config}
%define lbversion ${version}
%define cmtconfigrpm ${configrpm}

%global __os_install_post /usr/lib/rpm/check-buildroot

%define _topdir %{buildarea}/rpmbuild
%define tmpdir %{buildarea}/tmpbuild
%define _tmppath %{buildarea}/tmp

Name: %{projectUp}_%{lbversion}_%{cmtconfigrpm}
Version: %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Release: %{lhcb_release_version}
Vendor: LHCb
Summary: %{project}
License: GPL
Group: LHCb
BuildRoot: %{tmpdir}/%{name}-buildroot
BuildArch: noarch
AutoReqProv: no
Prefix: /opt/LHCbSoft
Provides: /bin/sh
Provides: %{projectUp}%{cmtconfig_rpm} = %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Requires: %{projectUp}_%{lbversion}

        \n""").substitute(buildarea = self._buildarea,
                          buildlocation = self._buildlocation,
                          project = self._project,
                          projectUp = self._project.upper(),
                          version = self._version,
                          config=self._cmtconfig,
                          configrpm=self._cmtconfig.replace('-', '_'),
                          rpmversion= self._version + "_" + self._cmtconfig.replace('-', '_'),
                          lhcb_maj_version = self._lhcb_maj_version,
                          lhcb_min_version = self._lhcb_min_version,
                          lhcb_patch_version = self._lhcb_patch_version,
                          lhcb_release_version = self._lhcb_release_version,
                          )

        return header


    def _createDataPackageDependency(self, pack, ver):
        '''
        Create the correct dependency line for the package
        '''
        # Looking up the package full info
        from LbConfiguration.Package import getPackage

        # Remove hat from package
        packonly = pack.split("/")[-1]
        p = getPackage(packonly)

        # Now parsing the version, including possible '*'
        if ver == '*':
            (major, minor, patch, gpatch) = ('*', None, None, None)
        else:
            _txt_version_style = r'v([0-9\*]+)r([0-9\*]+)(?:p([0-9\*]+))?(?:g([0-9\*]+))?'
            m = re.match(_txt_version_style, ver)
            if m == None:
                raise Exception("Version '%s' could not be parsed" % ver)
            (major, minor, patch, gpatch) = m.groups()
        
        if gpatch != None:
            raise Exception("Data package version %s not handled by RPM tools" % ver)

        reqstr = None
        if major == '*':
            # In this case we do not care about the version at all
            # We omit the version from the RPM req
            reqstr = "Requires: %s" %  p.tarBallName()
        elif minor == '*':
            # Classic vXr* for data packages
            # In that case we depend on the Provides with the major version number included
            reqstr = "Requires: %s_v%s" % (p.tarBallName(), major)
        elif patch != None:
            reqstr = "Requires: %s = %s.%s.%s" %  (p.tarBallName(), major, minor, patch)
        else:
            reqstr = "Requires: %s = %s.%s" %  (p.tarBallName(), major, minor)

        return reqstr + "\n"

    def _createRequires(self):
        '''
        Prepare the Requires section of the RPM
        '''
        tmp = ""

        # Dependencies to LHCb projects
        for (dproject, dversion) in self._manifest.getUsedProjects():
            tmp += "Requires: %s_%s_%%{cmtconfigrpm}\n" %  (dproject.upper(),
                                                            dversion)
        # Dependency to LCGCMT
        tmp += self._createHEPToolsRequires()

        # Dependency to data packages
        for (pack, ver) in self._manifest.getUsedDataPackages():
            tmp += self._createDataPackageDependency(pack, ver)

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
        spec += "mkdir -p ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/InstallArea/%{cmtconfig}\n"
        spec += "rsync -arL %{buildlocation}/%{projectUp}/%{projectUp}_%{lbversion}/InstallArea/%{cmtconfig} ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/InstallArea/\n"
        spec += "\n\n"
        return spec

    def _createTrailer(self):
        '''
        Prepare the RPM header
        '''
        trailer = Template("""
%post

%postun

%clean

%files
%defattr(-,root,root)
/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/InstallArea/%{cmtconfig}

%define date    %(echo `LC_ALL=\"C\" date +\"%a %b %d %Y\"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version
""").substitute(buildarea = self._buildarea,
                        project = self._project,
                        projectUp = self._project.upper(),
                        version = self._version,
                        config=self._cmtconfig,
                        configrpm=self._cmtconfig.replace('-', '_'),
                        rpmversion= self._version + "_" + self._cmtconfig.replace('-', '_'))

        return trailer
#
# Various utilities to extract info about the build
#
###############################################################################
def splitpath(path):
    ''' Split a path to all its components '''
    spath = []
    while True:
        (head, tail) = os.path.split(path)
        if len(head) == 0 or len(tail) == 0:
            break
        spath.insert(0, tail)
        path = head
    return spath

def getBuildInfo(manifestFileName):
    '''
    Get info about the build from the manifest filename itself
    '''
    realFilename = os.path.realpath(manifestFileName)
    splitPath = splitpath(realFilename)
    if len(splitPath) < 4 or splitPath[-3] != 'InstallArea':
        # The manifest is not in the standard location
        return (realFilename, None, None, None)
    else:
        barea = realFilename
        for i in range(5):
            barea = os.path.dirname(barea)
        return(realFilename, barea , splitPath[-4], splitPath[-2])



# Main Script to generate the spec file
#
###############################################################################
import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Script to generate the Spec file for an LHCb project.
    '''
    __usage__ = '%prog [options] <manifest.xml>'
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
        parser.add_option('-s', '--shared',
                          dest="shared",
                          default=False,
                          action="store_true",
                          help="Build shared RPM")
        parser.add_option('--shared-tar',
                          dest="sharedTar",
                          default=None,
                          action="store",
                          help="Shared tar to be included")
        parser.add_option('--builddir',
                          dest="builddir",
                          default=None,
                          action="store",
                          help="Force LCG dir if different from the one containing the config file")
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
            self.parser.error('wrong number of arguments')

        # Extracting info from filename
        filename = self.args[0]
        self.log.warning("Processing file %s" % filename)
        (absFilename, buildlocation, fprojectVersion, fcmtconfig) = getBuildInfo(filename)

        # Parsing the XML itself
        from LbTools.Manifest import Parser
        manifest = Parser(filename)

        (project, version) =  manifest.getProject()
        (LCGVerson, cmtconfig, lcg_system) = manifest.getHEPTools()

        buildarea = self.options.buildarea
        self.createBuildDirs(buildarea, project + "_" +  version + "_" + cmtconfig)
        if self.options.shared:
            spec = LHCbSharedRpmSpec(project, version, self.options.sharedTar, buildarea, buildlocation, manifest)
        else:
            spec = LHCbBinaryRpmSpec(project, version, cmtconfig, buildarea, buildlocation, manifest)

        if self.options.output:
            with open(self.options.output, "w") as outputfile:
                outputfile.write(spec.getSpec())
        else:
            print spec.getSpec()
