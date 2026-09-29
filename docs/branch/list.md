# branch list

List all local branches in alphabetical order, together with the files each branch has
changed relative to the base branch.

Files that appear on **more than one branch** are highlighted so you can spot potential
merge conflicts early.

---

## Usage

```
git-wrench branch list [--path <dir>] [--workspace]
```

| Option | Description |
|---|---|
| `--path <dir>` | Act on a specific directory (scanned up to `sync.recurse_depth`) |
| `--workspace` | Act on all configured workspaces instead of the current repo |

---

## Output

```
/home/user/projects/my-app  (base: develop)
  1. develop
      (base branch — skipped)
  2. feature/auth
      · src/auth.py
      · tests/test_auth.py
  3. feature/ui
      · src/auth.py          ← highlighted: also changed on feature/auth
      · src/ui.py
  4. fix/typo
      (no changed files)
```

- The **base branch** (first match from `rebase.branches_order`) is labelled and skipped
  in the diff.
- Files changed on multiple branches are printed in **yellow** as a conflict hint.
- If no base branch is found in the repo the diff cannot be computed and a note is shown.

---

## Configuration

The base branch is determined by `rebase.branches_order` in
`~/.config/git-wrench/config.toml`:

```toml
[rebase]
branches_order = ["develop", "main", "master"]
```

The first branch from this list that exists locally is used.

---

## See also

- [`branch gone`](gone.md) — delete stale tracking branches
- [`branch rebase`](rebase.md) — rebase all feature branches onto the base branch
