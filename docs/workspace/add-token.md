# workspace add-token

Interactively encrypt an API token with GPG and store the encrypted file path in the
workspace configuration.

---

## Usage

```
git-wrench workspace <name> add-token <server-name>
```

| Argument | Description |
|---|---|
| `<name>` | Name of the workspace |
| `<server-name>` | Name of the server whose token you are storing |

---

## How it works

1. Prompts for the API token (input is hidden — not echoed to the terminal).
2. Encrypts the token using `gpg --encrypt --armor --default-recipient-self`.
3. Writes the ASCII-armoured ciphertext to:
   ```
   ~/.config/git-wrench/<workspace>-<server>-token.asc
   ```
4. Saves the path of that file into the workspace's server entry in `config.toml`.

At runtime, whenever the token is needed (e.g. to fetch a repository list during
`sync`), git-wrench decrypts the file on the fly with `gpg --decrypt`.

---

## Prerequisites

- **GnuPG** must be installed (`gpg` must be on `PATH`).
- You must have a GPG key pair. Encryption uses `--default-recipient-self`, so your
  default key is used.

---

## Examples

```bash
# Store a GitHub personal access token for the "origin" server in workspace "work"
git-wrench workspace work add-token origin
# Token for server 'origin': <hidden input>
# Token encrypted and saved to: ~/.config/git-wrench/work-origin-token.asc
```

---

## Notes

- The plaintext token is never written to disk.
- If a token file already exists at the target path it will be overwritten.
- To rotate a token, simply run the command again with a new token value.

---

## See also

- [`workspace add-server`](add-server.md) — attach a server (you can provide a pre-existing token file with `--token`)
- [`workspace list-servers`](list-servers.md) — verify the token path is saved correctly
