# workspace list-servers

List the git servers that are attached to a workspace.

---

## Usage

```
git-wrench workspace <name> list-servers
git-wrench workspace <name> ls-servers    # alias
```

| Argument | Description |
|---|---|
| `<name>` | Name of the workspace |

---

## Output

```
  Name                 Type         URL                                       Token
  ────────────────────────────────────────────────────────────────────────────────
  origin               github       https://github.com/acme                   ~/.config/git-wrench/work-origin-token.asc
  internal             gitlab       https://git.acme.com
```

Columns:

| Column | Description |
|---|---|
| **Name** | The short server identifier |
| **Type** | `github`, `gitlab`, or `gitolite` |
| **URL** | Base URL of the server |
| **Token** | Path to the GPG-encrypted token file, if set |

---

## See also

- [`workspace add-server`](add-server.md) — attach a server
- [`workspace remove-server`](remove-server.md) — detach a server
- [`workspace add-token`](add-token.md) — store an API token
