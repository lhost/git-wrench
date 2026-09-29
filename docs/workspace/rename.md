# workspace rename

Rename an existing workspace.

---

## Usage

```
git-wrench workspace rename <old-name> <new-name>
git-wrench workspace mv     <old-name> <new-name>   # alias
```

| Argument | Description |
|---|---|
| `<old-name>` | Current name of the workspace |
| `<new-name>` | Desired new name |

---

## Examples

```bash
git-wrench workspace rename personal home
git-wrench workspace mv work acme
```

---

## Notes

- The path is not changed — only the name is updated.
- Returns an error if `<old-name>` does not exist or `<new-name>` is already taken.

---

## See also

- [`workspace list`](list.md) — view all workspaces
- [`workspace add`](add.md) — add a workspace
- [`workspace remove`](remove.md) — remove a workspace
