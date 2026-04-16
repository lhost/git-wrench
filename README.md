# Git Wrench 🔧

A command-line tool for automating common Git tasks.

## Commands

### `sync`

Synchronize Git repositories and keep your local workspace up to date.

```bash
git-wrench sync
```

### `status`

Display the current status of your Git repositories.

```bash
git-wrench status
```

### `workspace`

Manage and work with your Git workspace.

```bash
git-wrench workspace
```

## Project Structure

The command implementations are organized under the `git_wrench.commands` package:

```text
git_wrench/
├── commands/
│   ├── __init__.py
│   ├── sync.py
│   ├── status.py
│   └── workspace.py
└── ...
```

Each command is implemented in its own module, making the CLI easier to extend with additional Git automation commands.
