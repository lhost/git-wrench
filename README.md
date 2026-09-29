# git-wrench 🔧

A command-line tool for automating common Git tasks.

- **[Documentation](https://git-wrench.dev)**
- **[GitHub](https://github.com/lhost/git-wrench)**

---

## Features

| Feature | Description |
|---|---|
| **Interactive TUI** | Full-screen curses UI with tabbed navigation |
| **Repos tab** | Discover all git repos in your workspaces, see branch / ahead-behind / dirty state |
| **Sync** | Pull individual repos or all repos at once (fetch + fast-forward merge) |
| **Config tab** | Edit workspace paths and sync settings in-app, persisted to TOML |
| **CLI commands** | `sync` and `status` work without the TUI — pipe-friendly with ANSI output |
| **XDG config** | Follows `$XDG_CONFIG_HOME` standard |

---

## Installation

```bash
pip install .
# or, for development
pip install -e .
```

> Requires Python ≥ 3.14. The `curses` module is part of the standard library.

---

## Usage

See the **[full documentation](https://git-wrench.dev)** for detailed usage of all commands:

| Command | Docs |
|---|---|
| Interactive TUI | [git-wrench.dev](https://git-wrench.dev) |
| `sync` | [git-wrench.dev/workspace/sync/](https://git-wrench.dev/workspace/sync/) |
| `status` | [git-wrench.dev/workspace/status/](https://git-wrench.dev/workspace/status/) |
| `branch gone` | [git-wrench.dev/branch/gone/](https://git-wrench.dev/branch/gone/) |
| `branch list` | [git-wrench.dev/branch/list/](https://git-wrench.dev/branch/list/) |
| `branch rebase` | [git-wrench.dev/branch/rebase/](https://git-wrench.dev/branch/rebase/) |
| `workspace` | [git-wrench.dev/workspace/](https://git-wrench.dev/workspace/) |
| Configuration | [git-wrench.dev/config/](https://git-wrench.dev/config/) |
| Aliases | [git-wrench.dev/aliases/](https://git-wrench.dev/aliases/) |
