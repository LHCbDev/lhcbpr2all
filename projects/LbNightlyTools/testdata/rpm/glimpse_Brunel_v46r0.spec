
%define lhcb_maj_version 1
%define lhcb_min_version 0
%define lhcb_patch_version 0
%define lhcb_release_version 1
%define buildarea /tmp/lben/rpmdYu1k9
%define project Brunel
%define projectUp BRUNEL
%define lbversion v46r0

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

        
Requires: REC_v16r2_index
%description
%{project} glimpse indices

%install
mkdir -p ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}
cd  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb && tar jxf None 
mv  ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/.glimpse_filenames ${RPM_BUILD_ROOT}/opt/LHCbSoft/lhcb/%{projectUp}/%{projectUp}_%{lbversion}/.glimpse_filenames.config


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

%define date    %(echo `LC_ALL="C" date +"%a %b %d %Y"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version
