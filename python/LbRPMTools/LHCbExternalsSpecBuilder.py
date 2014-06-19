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
import logging
from string import Template
from subprocess import Popen, PIPE

from LHCbRPMSpecBuilder import LHCbBaseRpmSpec
from LbLegacy.Utils import getStatusOutput
from LbUtils.Temporary import TempDir
from LbUtils.CMT.Common import CMTCommand as CMT

tmpdir = TempDir(prefix="LHCbExternalsRpmSpec")

__log__ = logging.getLogger(__name__)

#
# Spec for binary RPMs
#
###############################################################################
class LHCbExternalsRpmSpec(LHCbBaseRpmSpec):
    """ Class representing a LHCb project"""

    def __init__(self, project, version, cmtconfig, buildarea, externalsDict, lcgVer):
        """ Constructor taking the actual file name """
        super(LHCbExternalsRpmSpec, self).__init__(project, version)
        __log__.debug("Creating RPM for %s/%s/%s" % (project, version, cmtconfig))
        self._project = project
        self._version = version
        self._cmtconfig = cmtconfig
        self._buildarea = buildarea
        self._externalsDict = externalsDict
        self._lcgVersion = lcgVer

    def _createHeader(self):
        '''
        Prepare the RPM header
        '''
        header = Template("""
%define lhcb_maj_version 1
%define lhcb_min_version 0
%define lhcb_patch_version 0
%define buildarea ${buildarea}
%define project ${project}
%define projectUp ${projectUp}
%define cmtconfig ${config}
%define lbversion ${version}
%define cmtconfigrpm ${configrpm}
%define lcgversion ${lcgversion}

%global __os_install_post /usr/lib/rpm/check-buildroot

%define _topdir %{buildarea}/rpmbuild
%define tmpdir %{buildarea}/tmpbuild
%define _tmppath %{buildarea}/tmp

Name: %{projectUp}_%{lbversion}_%{cmtconfigrpm}
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
Provides: %{project}_%{lcgversion}_%{cmtconfigrpm} = %{lhcb_maj_version}.%{lhcb_min_version}.%{lhcb_patch_version}

        \n""").substitute(buildarea = self._buildarea,
                          project = self._project,
                          projectUp = self._project.upper(),
                          version = self._version,
                          config=self._cmtconfig,
                          configrpm=self._cmtconfig.replace('-', '_'),
                          rpmversion= self._version + "_" + self._cmtconfig.replace('-', '_'),
                          lcgversion=self._lcgVersion)

        return header

    def _createRequires(self):
        '''
        Prepare the Requires section of the RPM
        '''
        tmp = ""
        for k,v in self._externalsDict.items():
            extVer = v[0]
            tmp += "Requires: LCG_%s_%s_%s_%s\n" % (self._lcgVersion, k, extVer, self._cmtconfig.replace('-', '_'))
            
        
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

        """).substitute(buildarea = self._buildarea,
                        project = self._project,
                        projectUp = self._project.upper(),
                        version = self._version,
                        config=self._cmtconfig,
                        configrpm=self._cmtconfig.replace('-', '_'),
                        rpmversion= self._version + "_" + self._cmtconfig.replace('-', '_'))

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
        if len(self.args) != 3:
            self.parser.error('wrong number of arguments')

        # Extracting info from filename
        project = self.args[0]
        version = self.args[1]
        cmtconfig = self.args[2]
        
        self.log.warning("Processing externals for %s %s %s" % (project, version, cmtconfig))

        buildarea = self.options.buildarea
        self.createBuildDirs(buildarea, project + "_" +  version + "_" + cmtconfig)

        (lcgVerTmp, externalsDict) =  get_native_versions(project.upper() + "_" + version, cmtconfig)
        lcgVer = lcgVerTmp.split("_")[1]

        import json
        with open('externalsDict.json', 'w') as outfile:
            json.dump(externalsDict, outfile)

        print "%s %s %s %s %s %s" % (project, version, cmtconfig, buildarea, externalsDict, lcgVer)
        
        spec = LHCbExternalsRpmSpec(project, version, cmtconfig, buildarea, externalsDict, lcgVer)

        if self.options.output:
            with open(self.options.output, "w") as outputfile:
                outputfile.write(spec.getSpec())
        else:
            print spec.getSpec()

#
# Utilities imported from mkLCGCMTtar to extract list of native versions
# from dependencies !
#
# BEWARE: This is a copy for code from mkLCGCMtar and it needs a lot of
#         cleanup before proper production.
#
###############################################################################
#  Method added to facilitate the lookup of macro values
def get_macro_value(cmtdir, macro, extratags):
    """ Returns the value of a macro """
    here = os.getcwd()
    if cmtdir != None:
        os.chdir(cmtdir)
    cmd = ["cmt", extratags, "show", "macro_value", macro]
    __log__.debug("get_macro_value - Running: ", " ".join(cmd))
    # Invoking popen to run the command, result is on stdout first line
    p = Popen(" ".join(cmd), stdout=PIPE, stderr=PIPE, shell=True)
    line = p.stdout.readline()[:-1]
    __log__.debug("get_macro_value - %s = %s" % (macro, line))
    if cmtdir != None:
        os.chdir(here)
    return line

def get_base_project(native_version):
    NAME = native_version.split('_')[0]
    version = native_version.split('_')[1]
    Name = NAME.lower().capitalize()
    if NAME == "LHCBDIRAC" :
        Name = "LHCbDirac"
    if NAME == 'LCGCMT':
        Name = 'LCG'
    if NAME == 'LHCBGRID' :
        Name = 'LHCbGrid'
    if Name == 'Lhcbexternals' :
        Name = 'LHCbExternals'
    NameSys = Name+'Sys'
    if Name == 'Gaudi':
        NameSys = Name+'Release'
    if Name == 'LCG' :
        NameSys = Name+'_Release'
    release_area = Name+'_release_area'
    if os.path.isdir(os.path.join(os.environ[release_area],Name+'Env',version)):
        os.chdir(os.path.join(os.environ[release_area],Name+'Env',version,'cmt'))
        if Name == 'Gaudi': NameSys = Name
    else:
        if not os.environ.has_key('CMTPROJECTPATH'):
            print 'you should set CMTPROJECTPATH first - STOP '
            sys.exit('No CMTPROJECTPATH')
        print 'CMTPROJECTPATH = ',os.environ['CMTPROJECTPATH']
        os.chdir(os.path.join(os.environ[release_area],NAME,native_version,'cmt'))
    print "get_base_project %s %s %s %s %s" % (NAME, version, Name, NameSys, release_area)
    return NAME, version, Name, NameSys, release_area


def get_project_dir(native_version):
    here = os.getcwd()
    NAME, version, Name, NameSys, release_area = get_base_project(native_version)
    dir = os.path.join(os.environ[release_area],NAME,native_version)
    os.chdir(here)
    return dir


def get_projectcmt_file(native_version):
    dir = get_project_dir(native_version)
    return os.path.join(dir,'cmt','project.cmt')

def get_runtime_deps(filename):
    deps = dict()
    matchexpr = re.compile("#\s*runtime_use\s+\w+")
    for l in open(filename, "r") :
        if matchexpr.search(l[:-1]) :
            words = l[:-1].replace("#","").split()
            if len(words) < 3 :
                deps[words[1]] = ""
            else :
                deps[words[1]] = words[2]
    return deps

def get_runtime_cmtpath(native_version):
    file = get_projectcmt_file(native_version)
    deps = get_runtime_deps(file)
    cmtpath = []
    for d in deps.keys():
        dir = get_project_dir(deps[d])
        cmtpath.append(dir)
    return ':'.join(cmtpath)


def get_cmtpath(native_version):
    os.environ['CMTPATH'] = get_runtime_cmtpath(native_version)
    status,CMTPATH = getStatusOutput('cmt show set_value CMTPATH')
    if CMTPATH[0] == ':' :
        CMTPATH = CMTPATH[1:]
    os.environ['CMTPATH'] = CMTPATH
    print 'CMTPATH=%s' % CMTPATH
    return CMTPATH

def get_lcg_version(cmtpath):
    for p in cmtpath.split(':') :
        pos = p.find('LCGCMT_')
        if pos != -1 :
            return p[pos:]

def getPackPrefix(pak, packages_versions, with_version=True):
    lcg_ext_loc = os.environ["LCG_external_area"]
    bin_dir = packages_versions[pak][2]
    nat_version = packages_versions[pak][0]
    pack_path = ""
    if len(packages_versions[pak]) > 3 :
        full_pack_path = os.path.normpath(packages_versions[pak][3])
        if full_pack_path.startswith(lcg_ext_loc + os.sep) :
            pack_path = full_pack_path.replace(lcg_ext_loc + os.sep, "")
    else :
        # special case for LCGCMT
        pack_path = os.sep.join([pak, nat_version])

    if bin_dir in pack_path :
        pack_path = pack_path[:pack_path.find(bin_dir)]

    if (not with_version) and nat_version :
        pack_path = pack_path[:pack_path.find(nat_version)]

    if pack_path.endswith(os.sep) :
        pack_path = pack_path[:-1]

    return pack_path

def getCMTExtraTags(binary):
    cmtargs = "-tag=LHCb,LHCbGrid"
    if  binary.startswith("win32") or binary.startswith("i686-winxp") :
        cmtargs = "-tag=LHCb,WIN32"
    elif  binary.startswith("win64") or binary.startswith("x86_64-winxp") :
        cmtargs = "-tag=LHCb,WIN64"
    else :
        if binary.find("slc3") != -1 :
            cmtargs = "-tag=LHCb,LHCbGrid,slc3"
    return cmtargs

def getLCGBinary(workdir, extname, binary):
    ext_home = CMT(getCMTExtraTags(binary), "show", "macro_value", "%s_home" % extname, cwd = workdir)[0][:-1]
    nat_version = CMT(getCMTExtraTags(binary), "show", "macro_value", "%s_native_version" % extname, cwd = workdir)[0][:-1]
    cfg_version = CMT(getCMTExtraTags(binary), "show", "macro_value", "%s_config_version" % extname, cwd = workdir)[0][:-1]
    if nat_version :
       ext_bin = None
       ext_bin_list = ext_home[ext_home.find(nat_version):].split(os.sep)
       if len(ext_bin_list) > 1 :
           ext_bin = ext_bin_list[1]
    else :
       ext_bin = ext_home.split(os.sep)[0]
    return nat_version, cfg_version, ext_bin, ext_home

def pkgFilter(NAME, pak, vers, binary):
    keep = True
    if NAME == "GANGA" and binary.find("slc5") != -1 :
        if pak == "Qt" and vers.startswith("3.") :
            keep = False
        if pak == "pyqt" and vers.startswith("3.") :
            keep = False
    if (binary.startswith("win32") or binary.find("winxp") != -1 )and pak == "pyqt_compat" :
        keep = False
    if pak.lower() == "icc" :
        keep = False
    if not keep :
        print "Excluding %s %s for %s" % (pak, vers, binary)
    return keep

def get_native_versions(native_version, binary):

    here = os.getcwd()
    packages_versions = {}
    extra_packages_versions = {}
    
    NAME, version, Name, NameSys, release_area = get_base_project(native_version)
    CMTPATH = get_cmtpath(native_version)
    lcgv = get_lcg_version(CMTPATH)
    native_cmt = os.path.join(os.environ[release_area], NAME, native_version, NameSys, 'cmt')
    if not os.path.exists(native_cmt) :
        native_cmt = os.path.join(os.environ[release_area], NAME, native_version, NameSys, version, 'cmt')
    os.chdir(native_cmt)
    __log__.debug('get_native_version - %s %s %s %s '%(release_area, native_cmt, os.getenv('CMTPATH'), lcgv))
    if NAME != 'LHCBGRID':
        packages_versions['LCGCMT'] = [lcgv, lcgv, binary]
    cmtshow = "cmt %s show " % getCMTExtraTags(binary)
    cmtcmd = cmtshow +'macros native > '

    # run cmtcmd

    natives = os.path.join(tmpdir.getName(), native_version+'.vers')
    __log__.debug('get_native_version - %s '%(cmtcmd+natives))

    os.system (cmtcmd+natives)

    # get packages_versions
    fd = open(natives)
    fdlines = fd.readlines()
    for fdline in fdlines:
        native = fdline.split('=')[0]
        pack = fdline.split('_native')[0]
        ext_info = getLCGBinary(native_cmt, pack, binary)
        vers = ext_info[0]
        if pkgFilter(NAME, pack, vers, binary) :
            packages_versions[pack] = list(ext_info)

    os.remove(natives)
    
    for pak in packages_versions.keys() :
        if not packages_versions[pak][0] :
            __log__.warning("%s has no version. Removing it from the list" % pak)
            del packages_versions[pak]

    # Code added to cope with the relocation of some packages from
    # external to app/releases (2012/06/14)

    # We first lookup the releases and external paths to be able to compare
    # this is dirty but we have no netter solution for the moment
    LCG_external = os.path.normpath(get_macro_value(None, "LCG_external", getCMTExtraTags(binary)))
    LCG_releases = os.path.normpath(get_macro_value(None, "LCG_releases", getCMTExtraTags(binary)))


    # Iterate over package to check whether they should be kept in external
    # or app/releases. We execute a show macro_value on the package home
    for pak in packages_versions.keys() :
        __log__.info("get_native_version - Checking home for package: %s" %  pak)
        macro = pak+ "_home"
        value = os.path.normpath(get_macro_value(None, macro, getCMTExtraTags(binary)))
        __log__.debug("get_native_version - %s = %s" % ( macro, value))

	# Performing the actual check between LCG_external and LCG_releases and the home of the
        # package
        # BEWARE: LCGCMT_home is set by CMT itself and can be incorrect !
        pakType = None
        if value.startswith(LCG_external):
            pakType = "external"
        if value.startswith(LCG_releases):
            pakType = "app/releases"

        # Compatibility check for OLD packages
        # Force external in this case
        if LCG_external == LCG_releases:
            print "get_native_version - *** Compatibility mode for OLD packages: setting the type to external ***"
            pakType = "external"

        if pakType is None:
        # Ignoring packages from the system
            if value.startswith("/usr"):
                print "get_native_version - %s home is %s, IGNORING package from system" % (pak, value)
                del packages_versions[pak]
            else:
                print "get_native_version - %s home is %s, not in external or app/releases, ABORTING" % (pak, value)
                sys.exit(1)
        else:
            # Adding the pakType to the attribute of the package in the map
            l = packages_versions[pak]
            l.append(pakType)
            print "get_native_version - Package %s is %s" % (pak, pakType)

    if binary.startswith("i686"):
        for pak in packages_versions.keys() :
            content = packages_versions[pak]
            if content[2].startswith("x86_64") :
                print "Replacing binary for %s" % pak
                newbin = content[2].replace("x86_64", "i686")
                newpath = content[3].replace("x86_64", "i686")
                packages_versions[pak] = [content[0], content[1], newbin, newpath, content[4]]

    os.chdir(here)
    return (lcgv, packages_versions)
