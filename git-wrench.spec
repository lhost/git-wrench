Name:           git-wrench
Version:        0.1.0
Release:        1%{?dist}
Summary:        Terminal-based multi-repo git workspace manager

License:        MIT
URL:            https://github.com/lhost/git-wrench
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-wheel
BuildRequires:  python3-build
BuildRequires:  python3-installer
BuildRequires:  python3-hatchling

Requires:       git
Requires:       python3
Requires:       python3-tomli-w

%description
git-wrench is a terminal-based multi-repo git workspace manager with an
interactive TUI and CLI commands to inspect status and synchronize repositories
across workspaces.

%prep
%autosetup -n %{name}-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files git_wrench

%check
%{py3_test_envvars} %{__python3} -m pytest

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/git-wrench

%changelog
* Sun Apr 19 2026 Lubomir Host <lubomir.host@gmail.com> - 0.1.0-1
- Initial RPM release
