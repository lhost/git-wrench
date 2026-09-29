# workspace add

Add a new named workspace.

---

## Usage

```
git-wrench workspace add <name> <path>
```

| Argument | Description |
|---|---|
| `<name>` | Short identifier for the workspace (e.g. `personal`, `work`) |
| `<path>` | Root directory to scan for git repositories. Tilde (`~`) is supported. |

---

## Examples

```bash
git-wrench workspace add personal ~/projects
git-wrench workspace add work ~/work/acme
git-wrench workspace add oss /opt/src/open-source
```

---

## Notes

- The name must be unique. Running the command again with the same name returns an error.
- The path is stored exactly as you type it (e.g. `~/projects`) and expanded at runtime.
- The workspace is written to `~/.config/git-wrench/config.toml` immediately.

---

## See also

- [`workspace list`](list.md) — view all workspaces
- [`workspace rename`](rename.md) — rename a workspace
- [`workspace remove`](remove.md) — remove a workspace
