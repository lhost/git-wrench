# branch rebase

Rebase local feature branches onto the configured base branch.

This is a convenience command for keeping many feature branches up to date when the base
branch moves forward frequently. It iterates over every local branch that is not itself a
base branch and runs `git rebase <base>` for each one.

---

## Usage

```
git-wrench branch rebase [--path <dir>] [--workspace] [--branch <b>] [--dry-run]
```

| Option | Description |
|---|---|
| `--path <dir>` | Act on a specific directory (scanned up to `sync.recurse_depth`) |
| `--workspace` | Act on all configured workspaces instead of the current repo |
| `--branch <b>` | Rebase only this specific local branch (default: all non-base branches) |
| `--dry-run` | Show what would be rebased without making any changes |

---

## What it does

1. Determines the **base branch** for the repo — the first branch from
   `rebase.branches_order` (`develop`, `main`, `master` by default) that exists locally.
2. Collects all local branches that are not in `branches_order` (or just the one given
   with `--branch`).
3. For each candidate branch, runs `git rebase <base>`.
   - Already-up-to-date branches are noted and counted as successes.
   - On conflict the rebase is automatically aborted (`git rebase --abort`) and the branch
     is left unchanged; the error is reported without stopping the remaining branches.

---

## Examples

```bash
# Rebase every feature branch in the current repo
git-wrench branch rebase

# Preview what would happen without making changes
git-wrench branch rebase --dry-run

# Rebase only one branch across all workspaces
git-wrench branch rebase --workspace --branch feature/my-ticket

# Rebase all branches in a specific workspace directory
git-wrench branch rebase --path ~/work/acme
```

---

## Configuration

```toml
[rebase]
branches_order = ["develop", "main", "master"]
```

The list is searched left-to-right; the first branch found locally in a repository is
used as the rebase target. Branches whose names appear in `branches_order` are never
rebased themselves.

---

## Notes

- The command does **not** check out the branch being rebased. It uses
  `git rebase <base> <branch>` with a detached approach, leaving your current checkout
  untouched.
- If a rebase fails (conflict), `git rebase --abort` is run automatically so the
  repository is always left in a clean state.
- Repos with no recognisable base branch (none of `branches_order` exists) are skipped
  with a notice.

---

## See also

- [`branch gone`](gone.md) — delete stale tracking branches
- [`branch list`](list.md) — see which files each branch has changed
