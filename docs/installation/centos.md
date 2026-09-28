# CentOS / RHEL installation

## Install the .rpm package (recommended)

Pre-built `.rpm` packages are published with each release on the
[GitHub Releases page](https://github.com/lhost/git-wrench/releases).

### 1. Install the dependency

git-wrench depends on `python3-tomli-w`. Install it first:

```shell
sudo dnf install -y python3-tomli-w git
```

### 2. Download and install the package

Replace `0.1.0` with the version you want to install:

```shell
VERSION=0.1.0
sudo dnf install -y https://github.com/lhost/git-wrench/releases/download/v${VERSION}/git-wrench-${VERSION}-1.noarch.rpm
```

### 3. Verify

```shell
git-wrench --help
```

---

## Build from source

To build the `.rpm` yourself from the repository:

```shell
# Install build dependencies
sudo dnf install -y rpm-build python3-devel python3-pip python3-wheel \
    python3-build python3-installer python3-hatchling make curl

# Clone the repository
git clone https://github.com/lhost/git-wrench.git
cd git-wrench

# Build the RPM
make rpm

# Install the resulting package
sudo dnf install -y dist/rpmbuild/RPMS/noarch/git-wrench-*.noarch.rpm
```

---

## Uninstall

```shell
sudo dnf remove git-wrench
```

---

## Other installation methods

- [Install with pipx](pipx.md)
- [Install with pip](pip.md)
