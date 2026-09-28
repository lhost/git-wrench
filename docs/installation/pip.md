# Install with pip

Use `pip` when you want to install git-wrench into an existing Python environment,
such as a project virtualenv or a CI image. For a system-wide install of a CLI tool,
[pipx](pipx.md) is usually a better choice.

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
    sudo apt-get install -y python3.14 python3.14-venv
    ```

=== "CentOS / RHEL"

    CentOS Stream 9 ships Python 3.9. Compile Python 3.14 from source or use a
    [community SCL](https://www.softwarecollections.org/) build for your distro.

---

## Install

```shell
pip install git+https://github.com/lhost/git-wrench.git
```

### Verify

```shell
git-wrench --help
```

---

## Update

```shell
pip install --upgrade git+https://github.com/lhost/git-wrench.git
```

---

## Uninstall

```shell
pip uninstall git-wrench
```
