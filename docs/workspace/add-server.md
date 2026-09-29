# workspace add-server

Attach a git server to a workspace so that `sync` can clone missing repositories
and detect stale ones.

---

## Usage

```
git-wrench workspace <name> add-server \
    --type <type> \
    [--token <path>] \
    <server-name> <url>
```

| Argument / Option | Description |
|---|---|
| `<name>` | Workspace to attach the server to |
| `--type <type>` | Server type: `github`, `gitlab`, or `gitolite` |
| `--token <path>` | Path to a GPG-encrypted API token file (optional; can be added later with [`add-token`](add-token.md)) |
| `<server-name>` | Short identifier for this server (e.g. `origin`, `internal`) |
| `<url>` | Base URL of the server (e.g. `https://github.com/acme`) |

---

## Supported server types

| Type | Notes |
|---|---|
| `github` | GitHub.com or GitHub Enterprise. Requires a personal access token with `repo` scope. |
| `gitlab` | GitLab.com or self-hosted GitLab. Requires a personal access token with `read_api` scope. |
| `gitolite` | Self-hosted Gitolite. Uses SSH-based repository listing (`ssh <host> info`). |

---

## Examples

```bash
# GitHub organisation — token stored separately later
git-wrench workspace work add-server --type github origin https://github.com/acme

# GitLab instance with token file provided up front
git-wrench workspace work add-server \
    --type gitlab \
    --token ~/.config/git-wrench/work-gitlab-token.asc \
    internal https://git.acme.com

# Gitolite server (no token needed — uses SSH keys)
git-wrench workspace work add-server --type gitolite git-server git@git.acme.com
```

---

## Notes

- The server name must be unique within the workspace.
- After adding a server you can run [`workspace add-token`](add-token.md) to encrypt and
  store an API token interactively.
- git-wrench uses the token only to fetch the repository list from the server API;
  actual `git clone` / `git fetch` operations rely on your normal SSH keys or
  credential helpers.

---

## See also

- [`workspace list-servers`](list-servers.md) — view attached servers
- [`workspace remove-server`](remove-server.md) — detach a server
- [`workspace add-token`](add-token.md) — store an API token
- [`sync`](sync.md) — clone and pull using server lists
