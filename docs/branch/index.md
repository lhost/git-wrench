# branch

Local branch management utilities.

By default every `branch` subcommand operates on the repository in the **current directory**.
Pass `--workspace` to act on all configured workspaces, or `--path` to target a specific
directory tree.

---

## Subcommands

| Subcommand | Description |
|---|---|
| [`gone`](gone.md) | Delete local branches whose remote tracking ref has been removed |
| [`list`](list.md) | List local branches with the files changed on each one |
| [`rebase`](rebase.md) | Rebase local branches onto the configured base branch |

---

## Quick reference

```
# Delete stale local branches (gone from remote)
git-wrench branch gone
git-wrench branch gone --workspace
git-wrench branch gone --force --yes

# List branches and their changed files
git-wrench branch list
git-wrench branch list --workspace

# Rebase all feature branches onto the base branch
git-wrench branch rebase
git-wrench branch rebase --workspace
git-wrench branch rebase --branch my-feature
git-wrench branch rebase --dry-run
```

---

## Shared options

All `branch` subcommands accept the following scope flags:

| Option | Description |
|---|---|
| `--path <dir>` | Act on a specific directory (scanned up to `sync.recurse_depth`) |
| `--workspace` | Act on all configured workspaces instead of the current repo |

When neither flag is given git-wrench acts only on the repository in `$PWD`.

---

## Configuration

The `[rebase]` section of `~/.config/git-wrench/config.toml` controls which branch is
treated as the base:

```toml
[rebase]
branches_order = ["develop", "main", "master"]
```

The first branch from this list that actually exists in the repository is used as the
**base branch** for both `branch list` (diff target) and `branch rebase` (rebase target).
