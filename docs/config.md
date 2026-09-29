# Configuration

git-wrench stores all settings in a single [TOML](https://toml.io) file.

**Default location**

```
~/.config/git-wrench/config.toml
```

If the environment variable `$XDG_CONFIG_HOME` is set, the file is placed there instead:

```
$XDG_CONFIG_HOME/git-wrench/config.toml
```

The file and its parent directory are **created automatically** with sensible defaults the first time git-wrench runs. You can edit it directly with any text editor, or manage workspaces with the [`workspace`](workspace/index.md) CLI commands.

---

## Full example

```toml
[workspaces]
list = [
    { name = "personal", path = "~/projects" },
    { name = "work",     path = "~/work" },
]

[sync]
recurse_depth     = 2
fetch_prune       = true
stash_before_pull = false

[rebase]
branches_order = ["develop", "main", "master"]
```

---

## `[workspaces]`

Defines the named root directories that git-wrench scans for repositories.

```toml
[workspaces]
list = [
    { name = "personal", path = "~/projects" },
    { name = "work",     path = "~/work/company" },
]
```

Each entry in `list` is an inline table with two required keys:

| Key | Type | Description |
|---|---|---|
| `name` | string | Short identifier used in CLI output and server sub-commands |
| `path` | string | Root directory to scan. Tilde (`~`) expansion is supported. |

Optionally, a workspace entry may contain a `servers` array for server-driven sync
(see [Workspace servers](#workspace-servers) below).

!!! note "Prefer the CLI"
    Use [`workspace add`](workspace/add.md), [`workspace rename`](workspace/rename.md),
    and [`workspace remove`](workspace/remove.md) to manage this list — the commands
    validate input and write the file atomically.

---

## `[sync]`

Controls how [`git-wrench sync`](workspace/sync.md) and [`git-wrench status`](workspace/status.md) discover and update repositories.

```toml
[sync]
recurse_depth     = 2
fetch_prune       = true
stash_before_pull = false
```

| Key | Type | Default | Description |
|---|---|---|---|
| `recurse_depth` | integer | `2` | How many directory levels below each workspace root to search for `.git` directories. Increase this if you nest repositories deeper than two levels. |
| `fetch_prune` | boolean | `true` | Pass `--prune` to `git fetch`, removing stale remote-tracking references. |
| `stash_before_pull` | boolean | `false` | Run `git stash` before pulling and `git stash pop` afterwards, so dirty working trees do not block the merge. |

---

## `[rebase]`

Controls which branch is treated as the **base branch** by [`git-wrench branch rebase`](branch/rebase.md) and [`git-wrench branch list`](branch/list.md).

```toml
[rebase]
branches_order = ["develop", "main", "master"]
```

| Key | Type | Default | Description |
|---|---|---|---|
| `branches_order` | list of strings | `["develop", "main", "master"]` | Candidate base-branch names in priority order. The first name that exists locally in a repository is used as the base. |

---

## Workspace servers

A workspace entry can carry an optional `servers` array. Each server entry enables
[`git-wrench sync`](workspace/sync.md) to fetch the full repository list from that server,
clone missing repos, and detect stale ones.

```toml
[workspaces]
list = [
    {
        name = "work",
        path = "~/work/acme",
        servers = [
            { server_type = "github",   server_name = "origin",   server_url = "https://github.com/acme" },
            { server_type = "gitlab",   server_name = "internal", server_url = "https://git.acme.com",    token = "~/.config/git-wrench/work-internal-token.asc" },
            { server_type = "gitolite", server_name = "legacy",   server_url = "git@git.acme.com" },
        ]
    },
]
```

Each server entry accepts:

| Key | Type | Required | Description |
|---|---|---|---|
| `server_type` | string | ✓ | One of `github`, `gitlab`, or `gitolite` |
| `server_name` | string | ✓ | Short identifier (e.g. `origin`, `internal`) |
| `server_url` | string | ✓ | Base URL of the server |
| `token` | string | — | Path to a GPG-encrypted API token file. Decrypted at runtime with `gpg --decrypt`. |

!!! note "Prefer the CLI for server management"
    Use [`workspace add-server`](workspace/add-server.md),
    [`workspace remove-server`](workspace/remove-server.md), and
    [`workspace add-token`](workspace/add-token.md) to manage server entries.
    The `add-token` command handles GPG encryption automatically.

---

## Defaults

Any key omitted from the file inherits the built-in default. git-wrench merges the on-disk
file *on top of* the defaults at load time, so you only need to include settings you want
to change.

The effective defaults are:

```toml
[workspaces]
list = [
    { name = "projects", path = "~/projects" },
]

[sync]
recurse_depth     = 2
fetch_prune       = true
stash_before_pull = false

[rebase]
branches_order = ["develop", "main", "master"]
```
