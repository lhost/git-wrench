# Install with pipx

[pipx](https://pipx.pypa.io) installs Python CLI tools into isolated virtual environments
so they never conflict with your system Python or other packages. It is the recommended
way to install git-wrench when you are not using a native package (`.deb`, `.rpm`,
Homebrew).

---

## Prerequisites

git-wrench requires **Python ≥ 3.14**. Check your version:

```shell
python3 --version
```

=== "macOS"

    Install Python 3.14 via Homebrew if needed:

    ```shell
    brew install python@3.14
    ```

=== "Debian / Ubuntu"

    Debian trixie ships Python 3.13. Install Python 3.14 from the
    [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa):

    ```shell
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install -y python3.14
    ```

=== "CentOS / RHEL"

    CentOS Stream 9 ships Python 3.9. Compile Python 3.14 from source or use a
    [community SCL](https://www.softwarecollections.org/) build for your distro.

---

## Install pipx

=== "macOS"

    ```shell
    brew install pipx
    pipx ensurepath
    ```

=== "Debian / Ubuntu"

    ```shell
    sudo apt-get install -y pipx
    pipx ensurepath
    ```

=== "CentOS / RHEL"

    ```shell
    sudo dnf install -y pipx
    pipx ensurepath
    ```

---

## Install git-wrench

```shell
pipx install git+https://github.com/lhost/git-wrench.git
```

### Verify

```shell
git-wrench --help
```

---

## Update

```shell
pipx upgrade git-wrench
```

---

## Uninstall

```shell
pipx uninstall git-wrench
```
