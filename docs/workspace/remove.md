# workspace remove

Remove a workspace from the configuration.

---

## Usage

```
git-wrench workspace remove <name>
git-wrench workspace rm     <name>    # alias
git-wrench workspace delete <name>    # alias
```

| Argument | Description |
|---|---|
| `<name>` | Name of the workspace to remove |

---

## Examples

```bash
git-wrench workspace remove personal
git-wrench workspace rm work
```

---

## Notes

- Only the configuration entry is removed — **no files or directories are deleted on disk**.
- Returns an error if the workspace name does not exist.

---

## See also

- [`workspace list`](list.md) — view all workspaces
- [`workspace add`](add.md) — add a workspace
- [`workspace rename`](rename.md) — rename a workspace
