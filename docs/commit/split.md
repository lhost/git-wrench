# commit split

Split git commits into smaller, logical chunks.

This command takes a commit (usually `HEAD`) and breaks its changes down into smaller, individual commits.
It is extremely useful during interactive rebases when you want to split a monolithic commit into clean, atomic pieces.

---

## Usage

```bash
git-wrench commit split <commit>
```

| Parameter | Description |
|---|---|
| `<commit>` | The commit to split. Must resolve to the current `HEAD` for safety. |

---

## What it does

The splitting behavior depends on how many files were modified in the commit:

### Case A: Multiple files in the commit
If the commit consists of multiple files, it is split **per file**:

1. Resets the index and working tree state to the parent of the commit (`HEAD~1`), leaving the modifications unstaged.
2. Stages and commits each file individually.
3. Appends the suffix ` - $filename` (e.g. ` - src/main.py`) to the original commit message.
4. Preserves the original author name, email, and date for each split commit.

### Case B: Only one file in the commit
If the commit contains changes to only a single file, it is split **per diff hunk**:

1. Resets the index and working tree state to the parent of the commit (`HEAD~1`).
2. Extracts individual hunks from the file's unified diff.
3. Stages and commits each hunk sequentially.
4. Appends the suffix ` - [idx/chunks_count]` (e.g. ` - [1/3]`) to the original commit message.
5. Preserves the original author name, email, and date for each split commit.

---

## Examples

```bash
# Split the current HEAD commit (e.g. while editing in an interactive rebase)
git-wrench commit split HEAD
```

---

## Notes

- **Current HEAD Safety Check**: To prevent accidentally altering or orphaning commits in your branch history, the command enforces that the `<commit>` argument matches the current `HEAD` commit of your branch.
- **Clean Repository Requirement**: The command requires a perfectly clean working directory (no unstaged or staged changes) before running. This prevents your active, uncommitted changes from accidentally being mixed with the commit being split.
- **Shorthand Alias**: To save typing, you can also run this command using the [`split`](../aliases.md#alias-split) alias:
  ```bash
  git-wrench split HEAD
  ```
