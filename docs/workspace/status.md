# status

Print a compact table showing the branch, ahead/behind counts, and dirty state for every
repository in your configured workspaces.

---

## Usage

```
git-wrench status [--path <dir>]
```

| Option | Description |
|---|---|
| `--path <dir>` | Scan a specific directory instead of configured workspaces |

---

## Output

```
Repository                                          Branch               ↑     ↓     Dirty
─────────────────────────────────────────────────────────────────────────────────────────
  /home/user/projects/api                           develop              0     2
  /home/user/projects/frontend                      feature/login        3     0     *
  /home/user/projects/infra                         main                 0     0
```

| Column | Description |
|---|---|
| **Repository** | Absolute path to the repository |
| **Branch** | Currently checked-out branch name (`?` if HEAD is detached or unknown) |
| **↑** | Commits ahead of the remote tracking branch |
| **↓** | Commits behind the remote tracking branch |
| **Dirty** | `*` if the working tree has uncommitted changes |

---

## Examples

```bash
# All configured workspaces
git-wrench status

# A one-off directory
git-wrench status --path ~/work/acme
```

---

## Notes

- `status` is read-only — it never modifies any repository.
- Ahead/behind counts require a remote tracking branch to be set up. If there is no
  upstream, both columns show `0`.
- The output is pipe-friendly (plain text with ANSI colour codes for dirty / unknown
  branches; columns are space-padded for easy `grep` / `awk` processing).

---

## See also

- [`sync`](sync.md) — pull all repos to bring them up to date
