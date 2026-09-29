# workspace remove-server

Detach a git server from a workspace.

---

## Usage

```
git-wrench workspace <name> remove-server  <server-name>
git-wrench workspace <name> rm-server      <server-name>    # alias
git-wrench workspace <name> delete-server  <server-name>    # alias
```

| Argument | Description |
|---|---|
| `<name>` | Name of the workspace |
| `<server-name>` | Name of the server to remove |

---

## Examples

```bash
git-wrench workspace work remove-server origin
git-wrench workspace work rm-server internal
```

---

## Notes

- Only the server entry is removed from the configuration — no local repositories
  are deleted and no remote data is changed.
- The encrypted token file (if any) is **not** deleted from disk; you can remove it
  manually if it is no longer needed.

---

## See also

- [`workspace list-servers`](list-servers.md) — view attached servers
- [`workspace add-server`](add-server.md) — attach a server
