
%define lhcb_maj_version 1
%define lhcb_min_version 0
%define lhcb_patch_version 0
%define lhcb_release_version 1
%define buildarea /tmp/lben/rpmsUn86r
%define project Brunel
%define projectUp BRUNEL
%define lbversion v46r0

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
cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb && getpack --no-eclipse-config --no-config -P -r Brunel v46r0


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
