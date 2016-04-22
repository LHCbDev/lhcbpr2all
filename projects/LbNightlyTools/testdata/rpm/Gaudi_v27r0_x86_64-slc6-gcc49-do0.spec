
%define lhcb_maj_version 1
%define lhcb_min_version 0
%define lhcb_patch_version 0
%define lhcb_release_version 2
%define buildarea /tmp/lben/rpm3xWw5p
%define buildlocation None
%define project Gaudi
%define projectUp GAUDI
%define cmtconfig x86_64-slc6-gcc49-do0
%define lbversion v27r0
%define cmtconfigrpm x86_64_slc6_gcc49_do0

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

        
Requires: LCGCMT_LCGCMT_83
Requires: LCG_83_AIDA_3.2.1_x86_64_slc6_gcc49_dbg
Requires: LCG_83_Boost_1.59.0_python2.7_x86_64_slc6_gcc49_dbg
Requires: LCG_83_CLHEP_2.3.1.1_x86_64_slc6_gcc49_dbg
Requires: LCG_83_CppUnit_1.12.1_p1_x86_64_slc6_gcc49_dbg
Requires: LCG_83_GSL_1.10_x86_64_slc6_gcc49_dbg
Requires: LCG_83_HepPDT_2.06.01_x86_64_slc6_gcc49_dbg
Requires: LCG_83_Python_2.7.9.p1_x86_64_slc6_gcc49_dbg
Requires: LCG_83_QMtest_2.4.1_python2.7_x86_64_slc6_gcc49_dbg
Requires: LCG_83_RELAX_RELAX_root6_x86_64_slc6_gcc49_dbg
Requires: LCG_83_ROOT_6.06.00_x86_64_slc6_gcc49_dbg
Requires: LCG_83_XercesC_3.1.1p1_x86_64_slc6_gcc49_dbg
Requires: LCG_83_doxygen_1.8.9.1_x86_64_slc6_gcc49_dbg
Requires: LCG_83_jemalloc_3.6.0_x86_64_slc6_gcc49_dbg
Requires: LCG_83_libunwind_5c2cade_x86_64_slc6_gcc49_dbg
Requires: LCG_83_pyanalysis_1.5_python2.7_x86_64_slc6_gcc49_dbg
Requires: LCG_83_pytools_1.9_python2.7_x86_64_slc6_gcc49_dbg
Requires: LCG_83_tbb_42_20140122_x86_64_slc6_gcc49_dbg
Requires: LCG_83_tcmalloc_2.4_x86_64_slc6_gcc49_dbg
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
