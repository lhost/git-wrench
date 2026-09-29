# workspace list

Print all workspaces that are currently configured.

---

## Usage

```
git-wrench workspace list
git-wrench workspace ls        # alias
```

No options are required. If no workspaces have been configured yet, a hint is printed
that explains how to add one.

---

## Output

```
  Name                      Path
  ────────────────────────────────────────────────────────────
  personal                  ~/projects
  work                      ~/work
```

Each row shows the workspace **name** and the raw **path** as it was stored (tilde
expansion is not applied to the display).

---

## See also

- [`workspace add`](add.md) — add a new workspace
- [`workspace remove`](remove.md) — remove a workspace
