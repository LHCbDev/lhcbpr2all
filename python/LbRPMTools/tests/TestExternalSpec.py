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
from os.path import normpath, join

class Test(unittest.TestCase):
    ''' Test cases for the RPM Spec builder '''

    def setUp(self):
        ''' Setup the test '''
        self._data_dir = normpath(join(*([__file__] + [os.pardir] * 4
                                         + ['testdata', 'rpm'])))

        self._externalsDictJSON = normpath(join(*([__file__] + [os.pardir] * 4
                                                  + ['testdata', 'rpm', 'LCG_68_externalsDict.json'])))

        logging.basicConfig(level=logging.INFO)

    def tearDown(self):
        ''' tear down the test '''
        pass

    def testExternalSpecBuilder(self):
        '''
        Test the externals package Spec Builder
        '''
        from LbRPMTools.LHCbExternalsSpecBuilder import LHCbExternalsRpmSpec

        project = "LHCbExternals"
        version = "v68r0"
        lcgVer = "68"
        platform = "x86_64-slc6-gcc48-opt"
        rpmbuildarea = "/tmp"
        externalsDict = None
        with open(self._externalsDictJSON, 'r') as infile:
            externalsDict = json.load(infile)


        spec = LHCbExternalsRpmSpec(project, version, platform, rpmbuildarea,
                                    externalsDict, lcgVer)
        spec.setRPMReleaseDir("/tmptoto")
        newspectxt = spec.getSpec()
        oldspectxt = '''
%define lhcb_maj_version 1
%define lhcb_min_version 0
%define lhcb_patch_version 0
%define buildarea /tmp
%define project LHCbExternals
%define projectUp LHCBEXTERNALS
%define cmtconfig x86_64-slc6-gcc48-opt
%define lbversion v68r0
%define cmtconfigrpm x86_64_slc6_gcc48_opt
%define lcgversion 68

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


Requires: LCG_68_sqlite_3070900_x86_64_slc6_gcc48_opt
Requires: LCG_68_expat_2.0.1_x86_64_slc6_gcc48_opt
Requires: LCG_68_Frontier_Client_2.8.10_x86_64_slc6_gcc48_opt
Requires: LCG_68_blas_20110419_x86_64_slc6_gcc48_opt
Requires: LCG_68_AIDA_3.2.1_x86_64_slc6_gcc48_opt
Requires: LCG_68_HepMC_2.06.08_x86_64_slc6_gcc48_opt
Requires: LCG_68_graphviz_2.28.0_x86_64_slc6_gcc48_opt
Requires: LCG_68_pyanalysis_1.4_python2.7_x86_64_slc6_gcc48_opt
Requires: LCG_68_mysql_5.5.27_x86_64_slc6_gcc48_opt
Requires: LCGCMT_LCGCMT_68
Requires: LCG_68_Boost_1.55.0_python2.7_x86_64_slc6_gcc48_opt
Requires: LCG_68_GSL_1.10_x86_64_slc6_gcc48_opt
Requires: LCG_68_GCCXML_0.9.0_20131026_x86_64_slc6_gcc48_opt
Requires: LCG_68_pygraphics_1.4_python2.7_x86_64_slc6_gcc48_opt
Requires: LCG_68_gcc_4.8.1_x86_64_slc6
Requires: LCG_68_neurobayes_expert_3.7.0_x86_64_slc6_gcc48_opt
Requires: LCG_68_CLHEP_1.9.4.7_x86_64_slc6_gcc48_opt
Requires: LCG_68_lapack_3.4.0_x86_64_slc6_gcc48_opt
Requires: LCG_68_Python_2.7.6_x86_64_slc6_gcc48_opt
Requires: LCG_68_pytools_1.8_python2.7_x86_64_slc6_gcc48_opt
Requires: LCG_68_HepPDT_2.06.01_x86_64_slc6_gcc48_opt
Requires: LCG_68_fastjet_3.0.6_x86_64_slc6_gcc48_opt
Requires: LCG_68_COOL_COOL_2_9_2_x86_64_slc6_gcc48_opt
Requires: LCG_68_ROOT_5.34.18_x86_64_slc6_gcc48_opt
Requires: LCG_68_XercesC_3.1.1p1_x86_64_slc6_gcc48_opt
Requires: LCG_68_Qt_4.8.4_x86_64_slc6_gcc48_opt
Requires: LCG_68_CORAL_CORAL_2_4_2_x86_64_slc6_gcc48_opt
Requires: LCG_68_xrootd_3.2.7_x86_64_slc6_gcc48_opt
Requires: LCG_68_libunwind_5c2cade_x86_64_slc6_gcc48_opt
Requires: LCG_68_tbb_42_20131118_x86_64_slc6_gcc48_opt
Requires: LCG_68_CppUnit_1.12.1_p1_x86_64_slc6_gcc48_opt
Requires: LCG_68_tcmalloc_1.7p3_x86_64_slc6_gcc48_opt
Requires: LCG_68_CASTOR_2.1.13_6_x86_64_slc6_gcc48_opt
Requires: LCG_68_vdt_0.3.6_x86_64_slc6_gcc48_opt
Requires: LCG_68_RELAX_RELAX_1_3_0p_x86_64_slc6_gcc48_opt
Requires: LCG_68_QMtest_2.4.1_python2.7_x86_64_slc6_gcc48_opt
Requires: LCG_68_fftw_3.1.2_x86_64_slc6_gcc48_opt
Requires: LCG_68_xqilla_2.2.4p1_x86_64_slc6_gcc48_opt
Requires: LCG_68_oracle_11.2.0.3.0_x86_64_slc6_gcc48_opt
%description
%{project}

%install



%files

%post

%postun

%clean

%define date    %(echo `LC_ALL="C" date +"%a %b %d %Y"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version
'''
        #print newspectxt

        nl = newspectxt.splitlines()
        ol = oldspectxt.splitlines()
        self.assertEquals(len(nl), len(ol))


        for i in range(len(ol)):
            if ol[i] != nl[i]:
                print "LINE[%d] REFERENCE:<%s>" % (i, ol[i])
                print "LINE[%d] GENERATED:<%s>" % (i, nl[i])
            self.assertEqual(nl[i], ol[i])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLoadXML']
    unittest.main()
