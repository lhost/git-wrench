# workspace

Manage named workspace definitions — the root directories git-wrench searches for repositories.

A **workspace** is a named pointer to a directory on disk. git-wrench scans each workspace
(up to [`sync.recurse_depth`](../index.md)) to discover git repositories when you run `sync`,
`status`, or `branch` commands.

Optionally a workspace can have one or more **git servers** attached to it.
When a server is configured, `sync` will fetch the server's full repository list, clone any
repos that are missing on disk, and warn about (or remove) repos that exist locally but are
no longer present on the server.

---

## Commands

| Command | Description |
|---|---|
| [`sync`](sync.md) | Pull all repos in configured workspaces |
| [`status`](status.md) | Show branch / ahead-behind / dirty state for all repos |
| [`list`](list.md) | Print all configured workspaces |
| [`add`](add.md) | Add a new workspace |
| [`rename`](rename.md) | Rename an existing workspace |
| [`remove`](remove.md) | Remove a workspace |
| [`list-servers`](list-servers.md) | List git servers attached to a workspace |
| [`add-server`](add-server.md) | Attach a git server to a workspace |
| [`remove-server`](remove-server.md) | Remove a git server from a workspace |
| [`add-token`](add-token.md) | Encrypt and store an API token for a server |

---

## Quick reference

```
git-wrench sync
git-wrench sync --path <dir>
git-wrench sync --clean

git-wrench status
git-wrench status --path <dir>

git-wrench workspace list
git-wrench workspace add   <name> <path>
git-wrench workspace rename <old-name> <new-name>
git-wrench workspace remove <name>

git-wrench workspace <name> list-servers
git-wrench workspace <name> add-server --type <type> [--token <path>] <server-name> <url>
git-wrench workspace <name> remove-server <server-name>
git-wrench workspace <name> add-token <server-name>
```

---

## Configuration

Workspaces are stored in the `[workspaces]` section of
`~/.config/git-wrench/config.toml`:

```toml
[workspaces]
list = [
    { name = "personal", path = "~/projects" },
    { name = "work",     path = "~/work" },
]
```

The file is updated automatically whenever you run an `add`, `rename`, or `remove` command.
