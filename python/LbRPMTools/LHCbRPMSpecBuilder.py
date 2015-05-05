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
from LbConfiguration.Version import extractVersion

__log__ = logging.getLogger(__name__)

PREFIX="/opt/LHCbSoft"

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
    def __init__(self, project, version, prodRPMReleaseDir="/afs/cern.ch/lhcb/distribution/rpm/lhcb"):
        self._project = project
        self._version = version
        self._lhcb_release_version = 0
        self._prodRPMReleaseDir = prodRPMReleaseDir

    def getSpec(self):
        """ Build the global spec file """

        # First we make sure we have a correct release number for the RPM
        # It is created at -1 in constructor.
        # At this point, we can check in the release directory if we need to bump up
        # the release number or keep the current one....
        self._setNextReleaseNumberFromRepo()

        # Now returning the spec itself...
        return str(self._createHeader()) \
               + str(self._createRequires()) \
               + str(self._createDescription()) \
               + str(self._createInstall()) \
               + str(self._createTrailer())

    def _createHEPToolsRequires(self):
        """ Creates the dependency on the HepTools (LHCbExternals) RPMs """
        heptools = self._manifest.getHEPTools()
        if heptools:
            (hver, hcmtconfig, packages) = heptools
            hcmtconfig = hcmtconfig.replace("-", "_")
            if packages:
                requires = ['Requires: LCGCMT_LCGCMT_{hver}\n'
                            .format(hver=hver)]
                requires += ['Requires: LCG_{hver}_{name}_{vers}_{platf}\n'
                             .format(hver=hver, name=name,
                                     vers=vers.replace('-', '_'),
                                     platf=hcmtconfig)
                             for name, vers in sorted(packages.items())]
                return ''.join(requires)
            else:
                return "Requires: LHCbExternals_%s_%s\n"  % (hver, hcmtconfig)
        else:
            return ""

    def _createExtToolsRequires(self):
        """ Creates the dependency on the external (middleware) RPMs """
        binary_tag, exttools = self._manifest.getExtTools()
        binary_tag = binary_tag.replace('-', '_')
        return ''.join('Requires: {name}_{vers}_{platf}\n'
                       .format(name=name, vers=vers.replace('-', '_'),
                               platf=binary_tag)
                       for name, vers in sorted(exttools.items()))


    def setRPMReleaseDir(self, rpmRelDir):
        """ Set the location for the RPM release directory """
        self._prodRPMReleaseDir = rpmRelDir

    def _setNextReleaseNumberFromRepo(self):
        """ Checks the RPM release dir (see constructor for the class) to find the
        next release number for the package.
        """
        if self._lhcb_release_version <= 0:
            if self._prodRPMReleaseDir != None and os.path.exists( self._prodRPMReleaseDir):
                __log__.warning("Looking for releases in %s" % self._prodRPMReleaseDir)
                # Getting the prefix of out RPM
                prefix = self.getRPMName(norelease = True)
                # Now getting the list of already released versions
                allfiles = [ f for f in os.listdir( self._prodRPMReleaseDir) if f.startswith(prefix)]
                # If the list is empty, release number is "1"...
                if len(allfiles) == 0:
                    __log__.warning("Did not find any releases in the directory - Release number is 1")
                    self._lhcb_release_version = 1
                else:
                    __log__.warning("Found %d files matching checking latest release" % len(allfiles) )
                    allrels = []
                    # Getting the releae numbers from the files found
                    for f in allfiles:
                        m = re.match("-(\d+)\.", f[len(prefix):])
                        if m != None:
                            allrels.append(int(m.group(1)))
                        else:
                            __log__.warning("Released RPM %s does not abide by naming convention for release" % f)

                    # Now checking the latest one and increase number
                    newrel = sorted(allrels)[-1] + 1
                    __log__.warning("New release is %d" % newrel)
                    self._lhcb_release_version = newrel

            else:
                # In the case the directory does not exist, still set it to one...
                self._lhcb_release_version = 1


#
# Spec for shared RPMs
#
###############################################################################
class LHCbSharedRpmSpec(LHCbBaseRpmSpec):
    """ Class representing the Spec file for an RPM containing the shared files for the project """

    def __init__(self, project, version, sharedTar, buildarea):
        """ Constructor  """
        super(LHCbSharedRpmSpec, self).__init__(project, version)
        __log__.debug("Creating Shared RPM for %s/%s" % (project, version))
        self._project = project
        self._version = version
        self._sharedTar = sharedTar
        self._buildarea = buildarea
        self._lhcb_maj_version = 1
        self._lhcb_min_version = 0
        self._lhcb_patch_version = 0
        self._lhcb_release_version = 0
        self._arch = "noarch"

    def getArch(self):
        ''' Return the architecture, always noarch for our packages'''
        return self._arch

    def getRPMName(self, norelease=False):
        ''' Return the architecture, always noarch for our packages'''
        projname =  "_".join([self._project.upper(), self._version])
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
Prefix: /opt/LHCbSoft
Provides: /bin/sh
Provides: %{projectUp}_%{lbversion} = %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}

        \n""").substitute(buildarea = self._buildarea,
                          project = self._project,
                          projectUp = self._project.upper(),
                          version = self._version,
                          lhcb_maj_version = self._lhcb_maj_version,
                          lhcb_min_version = self._lhcb_min_version,
                          lhcb_patch_version = self._lhcb_patch_version,
                          lhcb_release_version = self._lhcb_release_version,
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
            spec += "cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb && tar jxf %s" % self._sharedTar
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
# Spec for Extra shared RPMs
#
###############################################################################
class LHCbExtraSharedRpmSpec(LHCbBaseRpmSpec):
    """ Class representing the Spec file for an RPM containing the shared files for the project """

    def __init__(self, project, version, sharedTar, buildarea):
        """ Constructor  """
        super(LHCbExtraSharedRpmSpec, self).__init__(project, version)
        __log__.debug("Creating Shared RPM for %s/%s" % (project, version))
        self._project = project
        self._version = version
        self._sharedTar = sharedTar
        self._buildarea = buildarea
        self._lhcb_maj_version = 1
        self._lhcb_min_version = 0
        self._lhcb_patch_version = 0
        self._lhcb_release_version = 0
        self._arch = "noarch"

    def getArch(self):
        ''' Return the architecture, always noarch for our packages'''
        return self._arch

    def getRPMName(self, norelease=False):
        ''' Return the architecture, always noarch for our packages'''
        projname =  "_".join([self._project.upper(), self._version, "shared"])
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

%global __os_install_post /usr/lib/rpm/check-buildroot

%define _topdir %{buildarea}/rpmbuild
%define tmpdir %{buildarea}/tmpbuild
%define _tmppath %{buildarea}/tmp

Name: %{projectUp}_%{lbversion}_shared
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
Provides: %{projectUp}_%{lbversion}_shared = %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}

        \n""").substitute(buildarea = self._buildarea,
                          project = self._project,
                          projectUp = self._project.upper(),
                          version = self._version,
                          lhcb_maj_version = self._lhcb_maj_version,
                          lhcb_min_version = self._lhcb_min_version,
                          lhcb_patch_version = self._lhcb_patch_version,
                          lhcb_release_version = self._lhcb_release_version,
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
            spec += "cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb && tar jxf %s" % self._sharedTar
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
        self._cmtconfig = cmtconfig
        self._buildarea = buildarea
        self._buildlocation = buildlocation
        self._manifest = manifest
        # This is the version in LHCb Format
        self._version = version
        self._parsedVersion = extractVersion(version)
        # These are used for the main version of the package
        self._lhcb_maj_version = 1
        self._lhcb_min_version = 0
        self._lhcb_patch_version = 0
        self._lhcb_release_version = 0
        self._arch = "noarch"
        self._extraRequires = []

    def addExtraRequire(self, req):
        ''' Add a requirement for another package to the list '''
        self._extraRequires.append(req)

    def getExtraRequires(self):
        ''' Add a requirement for another package to the list '''
        return "\n".join([ "Requires: %s" % r for r in
                           self._extraRequires ])

    def getArch(self):
        ''' Return the architecture, always noarch for our packages'''
        return self._arch

    def getRPMName(self, norelease=False):
        ''' Return the architecture, always noarch for our packages'''
        projname =  "_".join([self._project.upper(),
                              self._version,
                              self._cmtconfig.replace('-', '_')])
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
Requires: %{projectUp}_%{lbversion}
${extraRequires}
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
                          extraRequires = self.getExtraRequires()
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

        # Now parsing the version, including possible '*' and 'v*'
        if ver in ('*', 'v*'):
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
        tmp += self._createExtToolsRequires()

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
# Spec for the glimpse RPMs
#
###############################################################################
class LHCbGlimpseRpmSpec(LHCbBaseRpmSpec):
    """ Class representing the Spec file for an RPM containing the shared files for the project """

    def __init__(self, project, version, sharedTar, buildarea, manifest):
        """ Constructor  """
        super(LHCbGlimpseRpmSpec, self).__init__(project, version)
        __log__.debug("Creating Shared RPM for %s/%s" % (project, version))
        self._project = project
        self._version = version
        self._sharedTar = sharedTar
        self._buildarea = buildarea
        self._lhcb_maj_version = 1
        self._lhcb_min_version = 0
        self._lhcb_patch_version = 0
        self._lhcb_release_version = 0
        self._manifest = manifest
        self._arch = "noarch"

    def getArch(self):
        ''' Return the architecture, always noarch for our packages'''
        return self._arch

    def getRPMName(self, norelease=False):
        ''' Return the architecture, always noarch for our packages'''
        projname =  "_".join([self._project.upper(), self._version, "index"])
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

%global __os_install_post /usr/lib/rpm/check-buildroot

%define _topdir %{buildarea}/rpmbuild
%define tmpdir %{buildarea}/tmpbuild
%define _tmppath %{buildarea}/tmp

Name: %{projectUp}_%{lbversion}_index
Version: %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Release: %{lhcb_release_version}
Vendor: LHCb
Summary: %{project} glimpse index
License: GPL
Group: LHCb
BuildRoot: %{tmpdir}/%{name}-buildroot
BuildArch: noarch
AutoReqProv: no
Prefix: /opt/LHCbSoft
Provides: /bin/sh
Provides: %{projectUp}_%{lbversion}_index = %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Requires: %{projectUp}_%{lbversion}

        \n""").substitute(buildarea = self._buildarea,
                          project = self._project,
                          projectUp = self._project.upper(),
                          version = self._version,
                          lhcb_maj_version = self._lhcb_maj_version,
                          lhcb_min_version = self._lhcb_min_version,
                          lhcb_patch_version = self._lhcb_patch_version,
                          lhcb_release_version = self._lhcb_release_version,
                          )

        return header

    def _createRequires(self):
        '''
        Prepare the Requires section of the RPM
        '''
        tmp = ""

        # Dependencies to LHCb projects
        for (dproject, dversion) in self._manifest.getUsedProjects():
            tmp += "Requires: %s_%s_index\n" %  (dproject.upper(),
                                                            dversion)
        return tmp

    def _createDescription(self):
        '''
        Prepare the Requires section of the RPM
        '''
        tmp  = "%description\n"
        tmp += "%{project} glimpse indices\n\n"
        return tmp

    def _createInstall(self):
        '''
        Prepare the Install section of the RPM
        '''
        spec = "%install\n"
        spec += "mkdir -p ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}\n"
        spec += "cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb && tar jxf %s \n" % self._sharedTar
        spec += "mv  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/.glimpse_filenames ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/.glimpse_filenames.config"

        spec += "\n\n"
        return spec

    def _createTrailer(self):
        '''
        Prepare the RPM header
        '''
        ###trailer = Template('''
        trailer = '''
%post

if [ "$MYSITEROOT" ]; then
PREFIX=$MYSITEROOT
else
PREFIX=%{prefix}
fi

echo "Fixing the file: ${PREFIX}/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/.glimpse_filenames.config"
REALPATH=$(cd $PREFIX/lhcb && /bin/pwd || echo $PREFIX/lhcb)
sed -e '2,$'"s|^|${REALPATH}/%{projectUp}/%{projectUp}_%{lbversion}/|" ${PREFIX}/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/.glimpse_filenames.config > ${PREFIX}/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/.glimpse_filenames

%postun

%clean

%files
%defattr(-,root,root)
/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}

%define date    %(echo `LC_ALL=\"C\" date +\"%a %b %d %Y\"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version
'''
        #).substitute(buildarea = self._buildarea,
        #                project = self._project,
        #                projectUp = self._project.upper(),
        #                version = self._version)


        return trailer



#
# Spec for Datapackage RPMs
#
###############################################################################
class LHCbDatapkgRpmSpec(LHCbBaseRpmSpec):
    """ Class representing the Spec file for an RPM containing the shared files for the project """

    def __init__(self, project, fulldatapkg, version, sharedTar, buildarea, release = 0):
        """ Constructor  """
        super(LHCbDatapkgRpmSpec, self).__init__(project, version)
        __log__.debug("Creating Shared RPM for %s/%s" % (project, version))
        self._project = project
        self._fulldatapkg = fulldatapkg
        if "/" in fulldatapkg:
            self._package = fulldatapkg.split("/")[-1]
        else:
            self._package = fulldatapkg
        self._normfulldatapkg =  fulldatapkg.replace("/", "_")
        self._fullname = "_".join([self._project.upper(),  self._normfulldatapkg])
        self._versiondir = os.path.join(self._project.upper(), self._fulldatapkg)
        self._version = version
        self._sharedTar = sharedTar
        self._buildarea = buildarea
        (self._lhcb_maj_version, self._lhcb_min_version, self._lhcb_patch_version) = parseVersion(version)
        self._lhcb_release_version = release
        self._arch = "noarch"

    def getArch(self):
        ''' Return the architecture, always noarch for our packages'''
        return self._arch

    def getRPMName(self, norelease=False):
        ''' Return the architecture, always noarch for our packages'''
        projname =  "_".join([self._project.upper(), self._normfulldatapkg])
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
%define normfulldatapkg ${normfulldatapkg}
%define fulldatapkg ${fulldatapkg}
%define fullname ${fullname}
%define package ${package}
%define lbversion ${version}
%define _postshell /bin/bash
%define prefix ${prefix}
%define versiondir ${versiondir}

%global __os_install_post /usr/lib/rpm/check-buildroot

%define _topdir %{buildarea}/rpmbuild
%define tmpdir %{buildarea}/tmpbuild
%define _tmppath %{buildarea}/tmp

Name: %{fullname}
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

Provides: %{package} = %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Provides: %{fullname} = %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Provides: %{package}_v%{lhcb_maj_version} = %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Provides: %{fullname}_v%{lhcb_maj_version} = %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}
Requires: %{projectUp}_common
Requires(post): LBSCRIPTS
Requires(post): COMPAT
        \n""").substitute(buildarea = self._buildarea,
                          project = self._project,
                          projectUp = self._project.upper(),
                          normfulldatapkg = self._normfulldatapkg,
                          fulldatapkg = self._fulldatapkg,
                          version = self._version,
                          lhcb_maj_version = self._lhcb_maj_version,
                          lhcb_min_version = self._lhcb_min_version,
                          lhcb_patch_version = self._lhcb_patch_version,
                          lhcb_release_version = self._lhcb_release_version,
                          fullname = self._fullname,
                          versiondir = self._versiondir,
                          package = self._package,
                          prefix = PREFIX
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
        tmp += "%{fullname} %{version}\n\n"
        return tmp

    def _createInstall(self):
        '''
        Prepare the Install section of the RPM
        '''
        spec = "%install\n"
        spec += "mkdir -p ${RPM_BUILD_ROOT}%{prefix}/lhcb/%{versiondir}\n"
        spec += "cd  ${RPM_BUILD_ROOT}%%{prefix}/lhcb && tar jxf %s" % self._sharedTar
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
        for _i in range(5):
            barea = os.path.dirname(barea)
        return(realFilename, barea , splitPath[-4], splitPath[-2])

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
        (_absFilename, buildlocation, _fprojectVersion, _fcmtconfig) = getBuildInfo(filename)

        # Parsing the XML itself
        from LbTools.Manifest import Parser
        manifest = Parser(filename)

        (project, version) =  manifest.getProject()
        (_LCGVerson, cmtconfig, _packages) = manifest.getHEPTools()

        buildarea = self.options.buildarea
        self.createBuildDirs(buildarea, project + "_" +  version + "_" + cmtconfig)
        if self.options.shared:
            spec = LHCbSharedRpmSpec(project, version, self.options.sharedTar, buildarea)
        elif self.options.glimpse:
            spec = LHCbGlimpseRpmSpec(project, version, self.options.sharedTar, buildarea,  manifest)
        else:
            spec = LHCbBinaryRpmSpec(project, version, cmtconfig, buildarea, buildlocation, manifest)

        if self.options.output:
            with open(self.options.output, "w") as outputfile:
                outputfile.write(spec.getSpec())
        else:
            print spec.getSpec()
