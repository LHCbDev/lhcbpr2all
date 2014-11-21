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
Class to generate RPM packages for a whole slot

Created on Feb 27, 2014

@author: Ben Couturier
'''

import os
import re
import logging
import shutil
from string import Template

__log__ = logging.getLogger(__name__)


# Main Script to generate the RPMs for a build slot
#
###############################################################################
import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Script to produce the RPM for a LHCb Nightly slot.
    '''
    __usage__ = '%prog [options] <slot_config.json>'
    __version__ = ''

    def addRpmOptions(self, parser):
        '''
        Add some basic (common) options to the option parser
        '''
        from optparse import OptionGroup
        group = OptionGroup(self.parser, "RPM Options")
        group.add_option('-p', '--platform',
                          dest="platform",
                          default=None,
                          action="store",
                          help="Force platform")
        group.add_option('-s', '--shared',
                          dest="shared",
                          default=False,
                          action="store_true",
                          help="Build shared RPM")
        group.add_option('-k', '--datapkg',
                          dest="datapkg",
                          default=False,
                          action="store_true",
                          help="Builds datapackage rpms")
        group.add_option('-g', '--glimpse',
                          dest="glimpse",
                          default=False,
                          action="store_true",
                          help="Build glimpse RPM")
        group.add_option('--shared-tar',
                          dest="sharedTar",
                          default=None,
                          action="store",
                          help="Shared tar to be included")
        group.add_option('--builddir',
                          dest="builddir",
                          default=None,
                          action="store",
                          help="Force LCG dir if different from the one containing the config file")
        group.add_option('-b', '--buildarea',
                          dest="buildarea",
                          default="/tmp",
                          action="store",
                          help="Force build root")
        group.add_option('-o', '--output',
                          dest="output",
                          default = None,
                          action="store",
                          help="File name for the generated specfile [default output to stdout]")
        group.add_option('--keep-rpmdir',
                         dest='keeprpmdir',
                         action= "store_true",
                         default = False,
                         help="Keep the directories used to build the RPMs")
        group.add_option('--dry-run',
                         dest='dryrun',
                         action= "store_true",
                         default = False,
                         help="Only prepare the spec, not the RPMs")
        group.add_option('--manifest',
                         dest="manifestfile",
                         default=None,
                         action="store",
                         help="Force the manifest file to be used")
        group.add_option('--rpmreldir',
                         dest="rpmreldir",
                         default=None,
                         action="store",
                         help="Specify the RPM release directory")

        parser.add_option_group(group)
        return parser

    def defineOpts(self):
        '''
        Prepare the option parser.
        '''
        from LbNightlyTools.ScriptsCommon import (addBasicOptions,
                                                  addDashboardOptions)

        addBasicOptions(self.parser)
        self.addRpmOptions(self.parser)

    def _createRpmDirs(self, buildarea, buildname):
        '''
        Create directories necessary to the build
        '''
        from LHCbRPMSpecBuilder import RpmDirConfig
        return RpmDirConfig(buildarea, buildname)

    def _callRpmbuild(self, specfilename, fullrpmpath, artifactdir):
        ''' Call the rpmbuild command itself '''

        if self.options.dryrun:
            self.log.warning("Dry run mode, not calling RPM build for %s" % specfilename)
            shutil.copy(specfilename, artifactdir)
            self.log.warning("Dry run mode, spec file copied to %s" % artifactdir)
            return

        # Now calling the rpmbuild command
        from subprocess import Popen, PIPE
        process = Popen(["rpmbuild", "-bb", specfilename],
                        stdout=PIPE, stderr=PIPE)

        (stdout, stderr) = process.communicate()
        # XXX Careful we should not be caching the stdout and stderr
        self.log.info(stdout)
        self.log.info(stderr)

        if not os.path.exists(fullrpmpath):
            self.log.error("Cannot find RPM: %s" % fullrpmpath)
            raise Exception("Cannot find RPM: %s" % fullrpmpath)
        else:
            self.log.info("Copying %s to %s" % (fullrpmpath, artifactdir))
            shutil.copy(fullrpmpath, artifactdir)

    def _getManifestFilename(self, builddir, project, version, platform):

        # Checking if the file was overriden (needed fro tests)
        if self.options.manifestfile != None:
            self.log.info("Using manifest.xml filename overriden to: %s" % self.options.manifestfile)
            return  self.options.manifestfile

        # Checking for the existence of the manifest.xml file
        projbuilddir = os.path.join(builddir, project.upper(), project.upper() + "_" + version)
        manifestxmlfile = os.path.join(projbuilddir, 'InstallArea', platform, 'manifest.xml')
        if not os.path.exists(manifestxmlfile):
            self.log.error("Missing manifest.xml file: %s" % manifestxmlfile)
            raise Exception("Missing manifest.xml file: %s" % manifestxmlfile)
        else:
            self.log.info("Using manifest.xml file: %s" % manifestxmlfile)
        return manifestxmlfile

    def _buildRpm(self, project, version, platform, rpmbuildarea, builddir, artifactdir, keeprpmdir):
        ''' Build the RPM for the project them and copy them to the target area '''

        # First check if there is a shared RPM to build
        hasShared = self._buildExtraSharedRpm(project, version, rpmbuildarea,
                                              artifactdir, keeprpmdir)

        rpmbuildname = "_".join([project, version, platform])

        # Creating the temp directories to prepare the RPMs
        rpmconf = self._createRpmDirs(rpmbuildarea, rpmbuildname)

        # Locating the manifest file
        manifestxmlfile =  self._getManifestFilename(builddir, project, version, platform)

        # Parsing the manifest.xml file
        from LbTools.Manifest import Parser

        manifest = Parser(manifestxmlfile)

        # Now generating the spec
        from LbRPMTools.LHCbRPMSpecBuilder import getBuildInfo
        from LbRPMTools.LHCbRPMSpecBuilder import LHCbBinaryRpmSpec
        (absFilename, buildlocation, fprojectVersion, fcmtconfig) = getBuildInfo(manifestxmlfile)
        spec = LHCbBinaryRpmSpec(project, version, platform, rpmbuildarea, buildlocation, manifest)
        spec.addExtraRequire( "_".join([project, version, 'shared']))

        # Check if a non default RPM release dir was specified
        if self.options.rpmreldir != None:
            self.log.warning("Setting RPM release dir from options: %s" % self.options.rpmreldir )
            spec.setRPMReleaseDir(self.options.rpmreldir)

        specfilename = os.path.join(rpmconf.topdir, rpmbuildname + ".spec" )
        with open(specfilename, "w") as outputfile:
            outputfile.write(spec.getSpec())

        # Building the name of the expected RPM
        rpmname =  spec.getRPMName()
        fullrpmpath = os.path.join(rpmconf.rpmsdir, spec.getArch(), rpmname)
        self._callRpmbuild(specfilename, fullrpmpath, artifactdir)

        # Remove tmpdirectory
        if not keeprpmdir:
            rpmconf.removeBuildArea()
            self.log.info("Removing: %s " % rpmconf.buildarea)
        else:
            self.log.info("Keeping: %s " % rpmconf.buildarea)



    def _buildExtraSharedRpm(self, project, version, rpmbuildarea, artifactdir, keeprpmdir):
        ''' Build the RPM for the extra shared tar filed produced by some projects
        like geant4 '''

        hasShared = False
        rpmbuildname = "_".join([project, version, 'shared'])

        # Creating the temp directories to prepare the RPMs
        rpmconf = self._createRpmDirs(rpmbuildarea, rpmbuildname)

        # Looking for archive with sources
        srcArchive = self._findExtraSharedArchive(project, version, artifactdir)
        if srcArchive != None:
            self.log.info("Taking sources from %s" % srcArchive)
            hasShared = True
        else:
            # No tar find, no need to do anything...
            hasShared = False
            return hasShared

        # Now generating the spec
        from LbRPMTools.LHCbRPMSpecBuilder import LHCbExtraSharedRpmSpec
        spec = LHCbExtraSharedRpmSpec(project, version, srcArchive, rpmbuildarea)
        # Check if a non default RPM release dir was specified
        if self.options.rpmreldir != None:
            self.log.warning("Setting RPM release dir from options: %s" % self.options.rpmreldir )
            spec.setRPMReleaseDir(self.options.rpmreldir)

        specfilename = os.path.join(rpmconf.topdir, rpmbuildname + ".spec" )
        with open(specfilename, "w") as outputfile:
            outputfile.write(spec.getSpec())

        # Building the name of the expected RPM
        rpmname =  spec.getRPMName()
        
        fullrpmpath = os.path.join(rpmconf.rpmsdir, spec.getArch(), rpmname)
        self._callRpmbuild(specfilename, fullrpmpath, artifactdir)

        # Remove tmpdirectory
        if not keeprpmdir:
            rpmconf.removeBuildArea()
            self.log.info("Removing: %s " % rpmconf.buildarea)
        else:
            self.log.info("Keeping: %s " % rpmconf.buildarea)



    def _buildSharedRpm(self, project, version, rpmbuildarea, artifactdir, keeprpmdir):
        ''' Build the RPM for the project them and copy them to the target area '''

        rpmbuildname = "_".join([project, version])

        # Creating the temp directories to prepare the RPMs
        rpmconf = self._createRpmDirs(rpmbuildarea, rpmbuildname)

        # Looking for archive with sources
        srcArchive = self._findSrcArchive(project, version, artifactdir)
        if srcArchive != None:
            self.log.info("Taking sources from %s" % srcArchive)
        else:
            self.log.warning("Doing clean checkout of the sources")

        # Now generating the spec
        from LbRPMTools.LHCbRPMSpecBuilder import LHCbSharedRpmSpec
        spec = LHCbSharedRpmSpec(project, version, srcArchive, rpmbuildarea)
        # Check if a non default RPM release dir was specified
        if self.options.rpmreldir != None:
            self.log.warning("Setting RPM release dir from options: %s" % self.options.rpmreldir )
            spec.setRPMReleaseDir(self.options.rpmreldir)

        specfilename = os.path.join(rpmconf.topdir, rpmbuildname + ".spec" )
        with open(specfilename, "w") as outputfile:
            outputfile.write(spec.getSpec())

        # Building the name of the expected RPM
        rpmname =  spec.getRPMName()
        fullrpmpath = os.path.join(rpmconf.rpmsdir, spec.getArch(), rpmname)
        self._callRpmbuild(specfilename, fullrpmpath, artifactdir)

        # Remove tmpdirectory
        if not keeprpmdir:
            rpmconf.removeBuildArea()
            self.log.info("Removing: %s " % rpmconf.buildarea)
        else:
            self.log.info("Keeping: %s " % rpmconf.buildarea)

    def _buildDatapkgRpm(self, project, fulldatapkg, version, rpmbuildarea, artifactdir, keeprpmdir):
        ''' Build the RPM for the datapkg and copy them to the target area '''
        fulldatapkg
        hat = None
        datapkg = fulldatapkg
        if "/" in datapkg:
            (hat, datapkg) = fulldatapkg.split("/")

        rpmbuildname = "_".join([project, datapkg ])

        # Creating the temp directories to prepare the RPMs
        rpmconf = self._createRpmDirs(rpmbuildarea, rpmbuildname)

        # Looking for archive with sources
        srcArchive = self._findDatapkgArchive(project, fulldatapkg, version, artifactdir)
        if srcArchive != None:
            self.log.info("Taking sources from %s" % srcArchive)
        else:
            self.log.warning("Doing clean checkout of the sources")

        # Now generating the spec
        from LbRPMTools.LHCbRPMSpecBuilder import LHCbDatapkgRpmSpec
        spec = LHCbDatapkgRpmSpec(project, fulldatapkg, version, srcArchive, rpmbuildarea)
        # Check if a non default RPM release dir was specified
        if self.options.rpmreldir != None:
            self.log.warning("Setting RPM release dir from options: %s" % self.options.rpmreldir )
            spec.setRPMReleaseDir(self.options.rpmreldir)
            
        specfilename = os.path.join(rpmconf.topdir, rpmbuildname + ".spec" )
        with open(specfilename, "w") as outputfile:
            outputfile.write(spec.getSpec())


        # Building the name of the expected RPM
        rpmname =  spec.getRPMName()
        fullrpmpath = os.path.join(rpmconf.rpmsdir, spec.getArch(), rpmname)
        self._callRpmbuild(specfilename, fullrpmpath, artifactdir)

        # Remove tmpdirectory
        if not keeprpmdir:
            rpmconf.removeBuildArea()
            self.log.info("Removing: %s " % rpmconf.buildarea)
        else:
            self.log.info("Keeping: %s " % rpmconf.buildarea)


    def _buildGlimpseRpm(self, project, version, platform, rpmbuildarea, builddir, artifactdir, keeprpmdir):
        ''' Build the RPM for glimpse index and copy them to the target area '''

        rpmbuildname = "_".join(["glimpse", project, version])

        # Creating the temp directories to prepare the RPMs
        rpmconf = self._createRpmDirs(rpmbuildarea, rpmbuildname)

        # Locating the manifest file
        manifestxmlfile =  self._getManifestFilename(builddir, project, version, platform)

        # Parsing the manifest.xml file
        from LbTools.Manifest import Parser

        manifest = Parser(manifestxmlfile)

        # Looking for archive with sources
        srcArchive = self._findGlimpseArchive(project, version, artifactdir)
        if srcArchive != None:
            self.log.info("Taking sources from %s" % srcArchive)
        else:
            self.log.warning("Doing clean checkout of the sources")

        # Now generating the spec
        from LbRPMTools.LHCbRPMSpecBuilder import LHCbGlimpseRpmSpec
        spec = LHCbGlimpseRpmSpec(project, version, srcArchive, rpmbuildarea, manifest)
        # Check if a non default RPM release dir was specified
        if self.options.rpmreldir != None:
            self.log.warning("Setting RPM release dir from options: %s" % self.options.rpmreldir )
            spec.setRPMReleaseDir(self.options.rpmreldir)

        specfilename = os.path.join(rpmconf.topdir, rpmbuildname + ".spec" )
        with open(specfilename, "w") as outputfile:
            outputfile.write(spec.getSpec())


        # Building the name of the expected RPM
        rpmname =  spec.getRPMName()
        fullrpmpath = os.path.join(rpmconf.rpmsdir, spec.getArch(), rpmname)
        self._callRpmbuild(specfilename, fullrpmpath, artifactdir)

        # Remove tmpdirectory
        if not keeprpmdir:
            rpmconf.removeBuildArea()
            self.log.info("Removing: %s " % rpmconf.buildarea)
        else:
            self.log.info("Keeping: %s " % rpmconf.buildarea)

    def _findGlimpseArchive(self, project, version, artifactdir):
        ''' Locate the source RPM '''
        # Checking if we find the src archive
        packname = [ project, version ]
        if self.options.build_id:
            packname.append(self.options.build_id)
        packname.append('index')
        packname.append('tar.bz2')
        archname =  '.'.join(packname)

        fullarchname = os.path.join(artifactdir, archname)
        self.log.info("Looking for file: %s" %  fullarchname)
        if os.path.exists(fullarchname):
            return os.path.abspath(fullarchname)
        else:
            return None

    def _findSrcArchive(self, project, version, artifactdir):
        ''' Locate the source RPM '''
        # Checking if we find the src archive
        packname = [ project, version ]
        if self.options.build_id:
            packname.append(self.options.build_id)
        packname.append('src')
        packname.append('tar.bz2')
        archname =  '.'.join(packname)

        fullarchname = os.path.join(artifactdir, archname)
        self.log.info("Looking for file: %s" %  fullarchname)
        if os.path.exists(fullarchname):
            return os.path.abspath(fullarchname)
        else:
            return None

    def _findExtraSharedArchive(self, project, version, artifactdir):
        ''' Locate the Extra Shared RPM '''
        # Checking if we find the src archive
        packname = [ project, version ]
        if self.options.build_id:
            packname.append(self.options.build_id)
        packname.append('shared')
        packname.append('tar.bz2')
        archname =  '.'.join(packname)

        fullarchname = os.path.join(artifactdir, archname)
        self.log.info("Looking for file: %s" %  fullarchname)
        if os.path.exists(fullarchname):
            return os.path.abspath(fullarchname)
        else:
            return None


    def _findDatapkgArchive(self, project, datapkg, version, artifactdir):
        ''' Locate the source RPM '''
        # Checking if we find the src archive
        fixeddatapkg = datapkg.replace("/", "_")
        packname = [ fixeddatapkg, version ]

        if self.options.build_id:
            packname.append(self.options.build_id)

        packname.append('src')
        packname.append('tar.bz2')
        archname =  '.'.join(packname)

        fullarchname = os.path.join(artifactdir, archname)
        self.log.info("Looking for file: %s" %  fullarchname)
        if os.path.exists(fullarchname):
            return os.path.abspath(fullarchname)
        else:
            return None


    def main(self):
        '''
        Main method for the script
        '''
        from LbNightlyTools.ScriptsCommon import expandTokensInOptions

        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        configfile = self.args[0]
        # Same logic as BuildSlot lo locate the builddir
        import os
        builddir = os.path.join(os.getcwd(), 'build')

        # Now loading the slot configuration
        from LbNightlyTools import Configuration
        self.config = Configuration.load(self.args[0])

        expandTokensInOptions(self.options, ['build_id', 'artifacts_dir'],
                              slot=self.config[u'slot'])

        # Check the final artifacts dir
        if self.options.artifacts_dir != None:
            artifactdir = self.options.artifacts_dir
        else:
            artifactdir =  os.path.join(os.getcwd(), 'artifacts')
            if not os.path.exists(artifactdir):
                os.makedirs(artifactdir)

        # Check plaform to package for
        import os
        platform = self.options.platform
        if platform == None:
            platform = os.environ.get("CMTCONFIG", None)
        if platform == None and not self.options.shared:
            raise Exception("Could not find platform")

        # temp area used to build the RPMs
        from tempfile import mkdtemp
        rpmbuildarea = mkdtemp(prefix="rpm")
        keeprpmdir = self.options.keeprpmdir

        if self.options.datapkg:
            for p in self.config["packages"]:
                fulldatapkg = p["name"]
                project = "DBASE" # by default..
                try:
                    project = p["container"]
                except:
                    # We can pass if not specified, default is DBASE
                    pass
                version = p["version"]
                self.log.info("Preparing RPM for datapkg %s %s %s" % (project, fulldatapkg, version))
                self._buildDatapkgRpm(project, fulldatapkg, version, rpmbuildarea, artifactdir, keeprpmdir)

            # Done we now exit...
            return


        for p in self.config["projects"]:
            project = p["name"]
            if ((self.options.projects and
                 project.lower() not in self.options.projects) or
                project.lower() in ('dbase', 'param')):
                self.log.warning("Skipping project %s" % project)
                continue # project not requested: skip
            version = p["version"]

            if self.options.shared:
                self.log.info("Preparing RPM for project %s %s %s" % (project, version, "src"))
                self._buildSharedRpm(project, version, rpmbuildarea, artifactdir, keeprpmdir)
            elif self.options.glimpse:
                self.log.info("Preparing Glimpse RPM for project %s %s" % (project, version))
                self._buildGlimpseRpm(project, version, platform, rpmbuildarea,  builddir, artifactdir, keeprpmdir)
            else:
                self.log.info("Preparing RPM for project %s %s %s" % (project, version, platform))
                self._buildRpm(project, version, platform, rpmbuildarea, builddir, artifactdir, keeprpmdir)

