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

### sync — pull all repos

```
git-wrench sync
git-wrench sync --path ~/my-workspace
git-wrench sync --clean
```

| Flag | Description |
|---|---|
| `--path <dir>` | Scan a specific directory instead of configured workspaces |
| `--clean` | Remove local repos not found on any configured server (prompts for confirmation) |

For workspaces with git servers configured, `sync` also fetches the server's repo list, clones any missing repos, and warns about (or with `--clean`, removes) repos that exist locally but are no longer on the server.

### status — repo overview table

```
git-wrench status
git-wrench status --path ~/my-workspace
```

### branch — local branch management

```
git-wrench branch gone
git-wrench branch gone --path ~/my-workspace
git-wrench branch gone --force
git-wrench branch gone --yes
```

Removes local branches whose remote tracking ref has been deleted (e.g. after a merged pull request is cleaned up on the server). Runs `git fetch --prune` first to refresh remote state, then lists all `[gone]` branches per repo and prompts for confirmation before deleting.

| Flag | Description |
|---|---|
| `--path <dir>` | Scan a specific directory instead of configured workspaces |
| `--force` | Delete with `-D` (removes even unmerged branches) |
| `--yes` | Skip the confirmation prompt |

### workspace — manage workspaces

```
git-wrench workspace list
git-wrench workspace add   <name> <path>
git-wrench workspace rename <old-name> <new-name>
git-wrench workspace remove <name>
git-wrench workspace <name> list-servers
git-wrench workspace <name> add-server --type <type> [--token <path>] <server-name> <url>
git-wrench workspace <name> remove-server <server-name>
git-wrench workspace <name> add-token <server-name>
```

### Help

```
git-wrench --help
git-wrench --help <command>
git-wrench <command> --help
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
├── bin
│   └── git-wrench         - executable script
├── git_wrench
│   ├── commands
│   │   ├── _ansi.py
│   │   ├── __init__.py
│   │   ├── branch.py
│   │   ├── status.py
│   │   ├── sync.py
│   │   └── workspace.py
│   ├── config.py          - TOML config load/save
│   ├── git_ops.py         - repo discovery & git operations
│   ├── __init__.py
│   ├── registry.py
│   ├── tui.py             - curses interactive interface
│   └── workspace.py       - workspace management
├── main.py                - CLI entrypoint
├── Makefile               - Makefile for development
├── pyproject.toml         - project metadata
├── README.md
├── tests
│ └── test_cli.py
```
