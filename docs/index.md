# git-wrench documentation


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
