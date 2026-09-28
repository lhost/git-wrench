# macOS installation

## Homebrew (recommended)

git-wrench is distributed via a Homebrew tap hosted on GitHub.

### Add the tap and install

```shell
brew tap lhost/git-wrench https://github.com/lhost/git-wrench
brew install git-wrench
```

### Verify

```shell
git-wrench --help
```

### Update

```shell
brew update && brew upgrade git-wrench
```

---

## Uninstall

```shell
brew uninstall git-wrench
brew untap lhost/git-wrench
```

---

## Other installation methods

- [Install with pipx](pipx.md)
- [Install with pip](pip.md)
