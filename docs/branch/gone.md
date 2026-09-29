# branch gone

Delete local branches whose remote tracking ref has been removed.

This is useful after merged pull requests are cleaned up on the server: the remote branch
is deleted, but `git branch -vv` still shows the local branch as `[origin/feature: gone]`.
`branch gone` finds and removes all such stale branches in one step.

---

## Usage

```
git-wrench branch gone [--path <dir>] [--workspace] [--force] [--yes]
```

| Option | Description |
|---|---|
| `--path <dir>` | Act on a specific directory (scanned up to `sync.recurse_depth`) |
| `--workspace` | Act on all configured workspaces instead of the current repo |
| `--force` | Delete branches with `git branch -D` (removes even unmerged branches) |
| `--yes` | Skip the confirmation prompt and delete immediately |

---

## What it does

1. Runs `git fetch --prune` to refresh the remote-tracking state.
2. Lists all local branches whose upstream is marked `[gone]` (i.e. `git branch -vv` output).
3. Prints the list and — unless `--yes` is given — prompts for confirmation.
4. Deletes confirmed branches with `git branch -d` (or `-D` if `--force` is set).

---

## Examples

```bash
# Current repo — interactive prompt
git-wrench branch gone

# All workspaces, skip prompt
git-wrench branch gone --workspace --yes

# Specific directory, force-delete even unmerged branches
git-wrench branch gone --path ~/work --force
```

---

## Notes

- Without `--force`, branches that have unmerged commits cannot be deleted
  (`git branch -d` refuses). Pass `--force` to override this safety check.
- If `git fetch --prune` fails for a repo (e.g. no network), that repo is skipped
  and counted as an error; other repos still proceed.

---

## See also

- [`branch list`](list.md) — see which files each branch has changed
- [`branch rebase`](rebase.md) — rebase feature branches onto the base branch
