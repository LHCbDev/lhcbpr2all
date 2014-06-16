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
'''

Test for the Tools generating Spec files

Created on Dec 3, 2013

@author: Ben Couturier
'''
import logging
import json
import os
import unittest
from os.path import normpath, join, exists

class Test(unittest.TestCase):
    ''' Test cases for the RPM Spec builder '''

    def setUp(self):
        ''' Setup the test '''
        self._data_dir = normpath(join(*([__file__] + [os.pardir] * 4
                                         + ['testdata', 'rpm'])))

        self._manifestfile = normpath(join(*([__file__] + [os.pardir] * 4
                                         + ['testdata', 'tools', 'manifest.xml'])))

        logging.basicConfig(level=logging.INFO)

    def tearDown(self):
        ''' tear down the test '''
        pass

    def testRpmDirConfig(self):
        '''
        Test the Rpm build area configuration
        '''
        from LbRPMTools.LHCbRPMSpecBuilder import RpmDirConfig
        from tempfile import mkdtemp

        # Create the dir structure
        mytmp = mkdtemp(prefix="toto")
        r = RpmDirConfig(mytmp, "app")

        # Assert the RPMS dir is there
        self.assertTrue(exists(join(mytmp, "rpmbuild", "RPMS")))

        # Now removing it
        r.removeBuildArea()
        # And check
        self.assertFalse(exists(join(mytmp)))


    def testBinarySpecBuilder(self):
        '''
        Test the binary package Spec Builder
        '''
        from LbRPMTools.LHCbRPMSpecBuilder import LHCbBinaryRpmSpec

        project = "TESTPROJECT"
        version = "v1r0"
        platform = "x86_64-slc6-gcc48-opt"
        rpmbuildarea = "rpmbuildarea"
        buildlocation = "buildlocation"

        from LbTools.Manifest import Parser
        manifest = Parser(self._manifestfile)
        
        spec = LHCbBinaryRpmSpec(project, version, platform, rpmbuildarea,
                                 buildlocation, manifest)

        newspectxt = spec.getSpec()
        oldspectxt = '''
%define lhcb_maj_version 1
%define lhcb_min_version 0
%define lhcb_patch_version 0
%define lhcb_release_version 1
%define buildarea rpmbuildarea
%define buildlocation buildlocation
%define project TESTPROJECT
%define projectUp TESTPROJECT
%define cmtconfig x86_64-slc6-gcc48-opt
%define lbversion v1r0
%define cmtconfigrpm x86_64_slc6_gcc48_opt

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

        
Requires: REC_HEAD_%{cmtconfigrpm}
Requires: TOTO_v1r1_%{cmtconfigrpm}
Requires: LHCbExternals_66_x86_64_slc6_gcc48_opt
Requires: DBASE_AppConfig_v3
Requires: DBASE_FieldMap_v5
Requires: PARAM_ParamFiles_v8
Requires: DBASE_PRConfig_v1
Requires: PARAM_QMTestFiles_v1
%description
%{project}

%install
mkdir -p ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/InstallArea/%{cmtconfig}
rsync -arL %{buildlocation}/%{projectUp}/%{projectUp}_%{lbversion}/InstallArea/%{cmtconfig} ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/InstallArea/



%post

%postun

%clean

%files
%defattr(-,root,root)
/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/InstallArea/%{cmtconfig}

%define date    %(echo `LC_ALL="C" date +"%a %b %d %Y"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version
'''    

        
        import sys
        nl = newspectxt.splitlines()
        ol = oldspectxt.splitlines()
        self.assertEquals(len(nl), len(ol))

        
        for i, l in enumerate(ol):
            self.assertEqual(nl[i], ol[i])
            if l != nl[i]:
                print "LINE[%d] NEW<%s>" % (i, l)
                print "LINE[%d] OLD<%s>" % (i, nl[i])
             



    def testSharedSpecBuilder(self):
        '''
        Test the shared package Spec Builder
        '''
        from LbRPMTools.LHCbRPMSpecBuilder import LHCbSharedRpmSpec

        project = "TESTPROJECT"
        version = "v1r0"
        platform = "x86_64-slc6-gcc48-opt"
        rpmbuildarea = "rpmbuildarea"
        buildlocation = "buildlocation"

        from LbTools.Manifest import Parser
        manifest = Parser(self._manifestfile)
        
        spec = LHCbSharedRpmSpec(project, version, "/tmp/toto.tar.gz", rpmbuildarea)

        newspectxt = spec.getSpec()
        oldspectxt = '''
%define lhcb_maj_version 1
%define lhcb_min_version 0
%define lhcb_patch_version 0
%define lhcb_release_version 1
%define buildarea rpmbuildarea
%define project TESTPROJECT
%define projectUp TESTPROJECT
%define lbversion v1r0

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

        
%description
%{project}

%install
mkdir -p ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}
cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb && tar jxf /tmp/toto.tar.gz


%post

%postun

%clean

%files
%defattr(-,root,root)
/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}

%define date    %(echo `LC_ALL="C" date +"%a %b %d %Y"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version
'''    

        
        import sys
        nl = newspectxt.splitlines()
        ol = oldspectxt.splitlines()
        self.assertEquals(len(nl), len(ol))
        
        for i, l in enumerate(ol):
            self.assertEqual(nl[i], ol[i])
            if l != nl[i]:
                print "LINE[%d] NEW<%s>" % (i, l)
                print "LINE[%d] OLD<%s>" % (i, nl[i])



    def testGlimpseSpecBuilder(self):
        '''
        Test the glimpse package Spec Builder
        '''
        from LbRPMTools.LHCbRPMSpecBuilder import LHCbGlimpseRpmSpec

        project = "TESTPROJECT"
        version = "v1r0"
        platform = "x86_64-slc6-gcc48-opt"
        rpmbuildarea = "rpmbuildarea"
        buildlocation = "buildlocation"

        from LbTools.Manifest import Parser
        manifest = Parser(self._manifestfile)
        
        spec = LHCbGlimpseRpmSpec(project, version, '/tmp/toto.tar.bz2',
                                  rpmbuildarea, manifest)

        newspectxt = spec.getSpec()
        oldspectxt = '''
%define lhcb_maj_version 1
%define lhcb_min_version 0
%define lhcb_patch_version 0
%define lhcb_release_version 1
%define buildarea rpmbuildarea
%define project TESTPROJECT
%define projectUp TESTPROJECT
%define lbversion v1r0

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

        
Requires: REC_HEAD_index
Requires: TOTO_v1r1_index
%description
%{project} glimpse indices

%install
mkdir -p ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}
cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb && tar jxf /tmp/toto.tar.bz2


%post

%postun

%clean

%files
%defattr(-,root,root)
/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}

%define date    %(echo `LC_ALL="C" date +"%a %b %d %Y"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version
'''    

        print newspectxt
        
        import sys
        nl = newspectxt.splitlines()
        ol = oldspectxt.splitlines()
        self.assertEquals(len(nl), len(ol))

        
        for i, l in enumerate(ol):
            self.assertEqual(nl[i], ol[i])
            if l != nl[i]:
                print "LINE[%d] NEW<%s>" % (i, l)
                print "LINE[%d] OLD<%s>" % (i, nl[i])
             
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLoadXML']
    unittest.main()
