# Command Aliases

To save typing, `git-wrench` provides convenient shorthand aliases for deeply nested subcommands.

These aliases map directly to their full counterpart commands:

---

## Alias `gone`

Shorthand alias for [`git-wrench branch gone`](branch/gone.md).

Delete local branches whose remote tracking ref has been removed

---

## Alias `rebase`

Shorthand alias for [`git-wrench branch rebase`](branch/rebase.md).

Rebase local branches onto the configured base branch

---

## Alias `split`

Shorthand alias for [`git-wrench commit split`](commit/split.md).

Split a git commit into smaller chunks (per file or per hunk)
