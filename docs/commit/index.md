# commit

Repository commit and splitting utilities.

By default, every `commit` subcommand operates on the repository in the **current directory**.

---

## Subcommands

| Subcommand | Description |
|---|---|
| [`split`](split.md) | Split a git commit into smaller chunks (per file or per hunk) |

---

## Quick reference

```bash
# Split the current HEAD commit into individual chunks
git-wrench commit split HEAD
```

---

## Shorthand Alias

To save typing, you can also run this command using the [`split`](../aliases.md#alias-split) alias:
```bash
git-wrench split HEAD
```
