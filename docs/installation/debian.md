# Debian installation

## Install the .deb package (recommended)

Pre-built `.deb` packages are published with each release on the
[GitHub Releases page](https://github.com/lhost/git-wrench/releases).

### 1. Install the dependency

git-wrench depends on `python3-tomli-w`. Install it first:

```shell
sudo apt-get update
sudo apt-get install -y python3-tomli-w git
```

### 2. Download and install the package

Replace `0.1.0` with the version you want to install:

```shell
VERSION=0.1.0
wget https://github.com/lhost/git-wrench/releases/download/v${VERSION}/git-wrench_${VERSION}-1_all.deb
sudo dpkg -i git-wrench_${VERSION}-1_all.deb
```

### 3. Verify

```shell
git-wrench --help
```

---

## Build from source

To build the `.deb` yourself from the repository:

```shell
# Install build dependencies
sudo apt-get install -y debhelper dh-python python3-all python3-hatchling \
    python3-installer python3-build pybuild-plugin-pyproject

# Clone and build
git clone https://github.com/lhost/git-wrench.git
cd git-wrench
dpkg-buildpackage -us -uc -b

# Install the resulting package
sudo dpkg -i ../git-wrench_*.deb
```

---

## Uninstall

```shell
sudo apt-get remove git-wrench
```

---

## Other installation methods

- [Install with pipx](pipx.md)
- [Install with pip](pip.md)
