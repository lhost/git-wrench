# git-wrench 🔧

A command-line tool for automating common Git tasks.

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

> Requires Python ≥ 3.13. The `curses` module is part of the standard library.

---

## Usage

### Interactive TUI

```
git-wrench
```

Launches the full-screen interface.

**Keyboard shortcuts:**

| Key | Action |
|---|---|
| `Tab` / `Shift-Tab` | Switch between tabs (Repos / Config / Help) |
| `↑` / `↓` | Move cursor |
| `Enter` | Sync selected repo / edit config setting |
| `a` | Sync **all** repos |
| `r` | Refresh the repo list |
| `q` / `Esc` | Quit |

## Commands

### CLI – sync all repos

```
git-wrench sync
git-wrench sync --path ~/my-workspace
```

### CLI – status overview

```
git-wrench status
git-wrench status --path ~/my-workspace
```

### Help

```
git-wrench --help
```

---

## Configuration

Config file is stored at:

```
~/.config/git-wrench/config.toml
$XDG_CONFIG_HOME/git-wrench/config.toml   (if $XDG_CONFIG_HOME is set)
```

Created automatically with defaults on first run. Example:

```toml
[workspaces]
paths = [
    "~/projects",
    "~/work",
]

[sync]
recurse_depth = 2        # how deep to search for .git directories
fetch_prune = true       # pass --prune to git fetch
stash_before_pull = false
```

You can edit the file directly or use the **Config** tab in the TUI.

---

## Project layout

```
git_wrench/
├── commands/
│   ├── __init__.py
│   ├── sync.py
│   ├── status.py
│   └── workspace.py
├── config.py      – TOML config load/save
├── git_ops.py     – repo discovery & git operations
├── commands.py    – CLI command implementations (sync, status)
├── tui.py         – curses interactive interface
├── main.py        – entry point / command dispatcher
├── pyproject.toml - project metadata
└── ...
```
