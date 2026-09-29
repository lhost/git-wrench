# sync

Pull all repositories in configured workspaces.

When a workspace has **git servers** attached, `sync` also fetches the full repository
list from each server, clones any repos that are missing on disk, and can optionally
remove repos that exist locally but are no longer present on any server.

---

## Usage

```
git-wrench sync [--path <dir>] [--clean]
```

| Option | Description |
|---|---|
| `--path <dir>` | Scan a specific directory instead of configured workspaces |
| `--clean` | Prompt to remove local repos not found on any configured server |

---

## What it does

### Without server configuration

1. Discovers all git repositories in each workspace (up to `sync.recurse_depth`).
2. For each repo: optionally stashes uncommitted changes, runs `git fetch` (with
   `--prune` if `fetch_prune = true`), then fast-forward merges the current branch.

### With server configuration

1. Connects to each configured server and retrieves its repository list.
2. **Clones** any repo that is listed on the server but not yet on disk.
3. **Warns** (or with `--clean`, **removes**) repos on disk that no longer appear on
   any configured server.
4. **Pulls** all remaining repos as in the no-server case.

---

## Examples

```bash
# Pull every workspace
git-wrench sync

# Pull a one-off directory (no workspace config needed)
git-wrench sync --path ~/tmp/repos

# Clone missing repos and clean up stale ones
git-wrench sync --clean
```

---

## Configuration

```toml
[sync]
recurse_depth     = 2      # how deep to scan for .git directories
fetch_prune       = true   # pass --prune to git fetch
stash_before_pull = false  # stash uncommitted changes before pulling
```

- **`recurse_depth`** — controls how many directory levels below each workspace root
  git-wrench searches for `.git` directories. Set higher if you nest repos deeper.
- **`fetch_prune`** — removes stale remote-tracking references during fetch.
- **`stash_before_pull`** — when `true`, runs `git stash` before pulling and
  `git stash pop` afterwards so dirty working trees do not block the merge.

---

## Notes

- Only **fast-forward** merges are performed. If a branch has diverged and cannot be
  fast-forwarded, the repo is marked as an error and left unchanged.
- Repos that were just cloned are skipped in the pull phase (they are already up to date).
- A depth warning is printed when a remote repo path is deeper than `recurse_depth`
  — the repo will be cloned but then not found during the pull scan.

---

## See also

- [`status`](status.md) — view the current state of all repos without pulling
- [`workspace add-server`](add-server.md) — attach a git server for auto-clone
- [`workspace add-token`](add-token.md) — store an API token for server access
