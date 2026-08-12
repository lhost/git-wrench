"""
git-wrench branch — local branch management utilities.

By default both subcommands operate on the repository in the current directory.
Pass --path or --workspace to act on a broader scope.

Subcommands:
  gone    Delete local branches whose remote tracking ref has been removed.
          Runs 'git fetch --prune' first to refresh remote tracking state,
          then lists branches marked as '[gone]' and prompts before deletion.

  list    List all local branches in alphabetical order (numbered) together
          with the files changed on each branch relative to the base branch

  rebase  Rebase local branches onto the first base branch found in
          rebase.branches_order (config default: develop, main, master).
          Base branches themselves and already-up-to-date branches are skipped.

Options (both subcommands):
  --path <dir>   Act on a specific directory (scanned up to recurse_depth)
  --workspace    Act on all configured workspaces instead of the current repo

Options (gone):
  --force        Delete branches with 'git branch -D' (unmerged branches too)
  --yes          Skip confirmation prompt and delete immediately

Options (list):
  (none beyond the shared --path / --workspace)

Options (rebase):
  --branch <b>   Rebase only this specific local branch (default: all non-base branches)
  --dry-run      Show what would be rebased without making any changes

Configuration:
  [rebase]
  branches_order = ["develop", "main", "master"]   # first one found is used as the base

Usage:
  git-wrench branch gone
  git-wrench branch gone --workspace
  git-wrench branch gone --path ~/my-workspace
  git-wrench branch gone --force
  git-wrench branch gone --yes

  git-wrench branch list
  git-wrench branch list --workspace
  git-wrench branch list --path ~/my-workspace

  git-wrench branch rebase
  git-wrench branch rebase --workspace
  git-wrench branch rebase --path ~/my-workspace
  git-wrench branch rebase --branch my-feature
  git-wrench branch rebase --dry-run
"""

from __future__ import annotations

import sys
from pathlib import Path

from git_wrench.commands._ansi import BOLD, CYAN, DIM, GREEN, RED, YELLOW
from git_wrench.registry import command


@command("branch", help="Local branch management (gone, rebase, …)", long_help=__doc__)
def run(args: list[str]) -> int:
    if not args or args[0] in ("-h", "--help"):
        print((__doc__ or "").strip())
        return 0

    subcmd, rest = args[0], args[1:]

    if subcmd == "gone":
        return _gone(rest)
    if subcmd == "list":
        return _list(rest)
    if subcmd == "rebase":
        return _rebase(rest)

    print(RED(f"git-wrench branch: unknown subcommand '{subcmd}'."), file=sys.stderr)
    print(DIM("Run 'git-wrench branch --help' for usage."), file=sys.stderr)
    return 1


# ── shared arg helpers ────────────────────────────────────────────────────────


def _resolve_roots(
    override_path: Path | None,
    use_workspace: bool,
    conf: dict,
    depth: int,
) -> tuple[list[Path], int]:
    """Return (roots, effective_depth) based on how the user scoped the command.

    Priority:
      1. --path <dir>   → that directory, scanned up to recurse_depth
      2. --workspace    → all configured workspace paths, scanned up to recurse_depth
      3. (default)      → current working directory only (depth=0, i.e. this repo)
    """
    from git_wrench import config as cfg

    if override_path is not None:
        return [override_path], depth
    if use_workspace:
        return cfg.workspace_paths(conf), depth
    # default: current repo only
    return [Path.cwd()], 0


# ── gone ──────────────────────────────────────────────────────────────────────


def _gone(args: list[str]) -> int:
    """Remove local branches whose upstream tracking ref is gone."""
    from git_wrench import config as cfg
    from git_wrench import git_ops

    override_path: Path | None = None
    use_workspace = False
    force = False
    yes = False
    i = 0
    while i < len(args):
        if args[i] in ("--path", "-p") and i + 1 < len(args):
            override_path = Path(args[i + 1]).expanduser().resolve()
            i += 2
        elif args[i] == "--workspace":
            use_workspace = True
            i += 1
        elif args[i] == "--force":
            force = True
            i += 1
        elif args[i] == "--yes":
            yes = True
            i += 1
        else:
            i += 1

    conf = cfg.load()
    sync_cfg = conf.get("sync", {})
    depth = int(sync_cfg.get("recurse_depth", 2))

    roots, effective_depth = _resolve_roots(override_path, use_workspace, conf, depth)
    if not roots:
        print(RED("No workspace paths configured. Run 'git-wrench' interactively to add one."))
        return 1

    print(BOLD("git-wrench branch gone"))

    repos = git_ops.find_repos(roots, max_depth=effective_depth)
    if not repos:
        print(YELLOW("No git repositories found."))
        return 0

    global_err = 0

    for repo in repos:
        # Fetch + prune so remote tracking state is up to date.
        sys.stdout.write(f"  {CYAN(str(repo.path) + ' '):.<60} fetching… ")
        sys.stdout.flush()
        rc, _, err = git_ops._run(["git", "fetch", "--prune"], repo.path)
        if rc != 0:
            print(RED(f"✗ fetch failed: {err}"))
            global_err += 1
            continue
        print(DIM("ok"))

        gone = git_ops.gone_branches(repo.path)
        if not gone:
            continue

        print(YELLOW(f"    {len(gone)} gone branch(es) in {repo.path}:"))
        for b in gone:
            print(f"      {CYAN(b)}")

        if not yes:
            answer = input("    Delete them? [y/N] ").strip().lower()
            if answer != "y":
                print(DIM("    Skipped."))
                continue

        delete_flag = "-D" if force else "-d"
        deleted = failed = 0
        for b in gone:
            rc, _, err = git_ops._run(["git", "branch", delete_flag, b], repo.path)
            if rc == 0:
                print(GREEN(f"    ✓ deleted {b}"))
                deleted += 1
            else:
                print(RED(f"    ✗ could not delete {b}: {err}"))
                failed += 1
                global_err += 1

        print(DIM(f"    {deleted} deleted, {failed} failed."))

    return 0 if global_err == 0 else 1


# ── list ──────────────────────────────────────────────────────────────────────


def _list(args: list[str]) -> int:
    """List all local branches (alphabetically, numbered) with changed files."""
    from git_wrench import config as cfg
    from git_wrench import git_ops

    override_path: Path | None = None
    use_workspace = False
    i = 0
    while i < len(args):
        if args[i] in ("--path", "-p") and i + 1 < len(args):
            override_path = Path(args[i + 1]).expanduser().resolve()
            i += 2
        elif args[i] == "--workspace":
            use_workspace = True
            i += 1
        else:
            i += 1

    conf = cfg.load()
    sync_cfg = conf.get("sync", {})
    rebase_cfg = conf.get("rebase", {})
    depth = int(sync_cfg.get("recurse_depth", 2))
    branches_order: list[str] = rebase_cfg.get("branches_order", ["develop", "main", "master"])

    roots, effective_depth = _resolve_roots(override_path, use_workspace, conf, depth)
    if not roots:
        print(RED("No workspace paths configured. Run 'git-wrench' interactively to add one."))
        return 1

    print(BOLD("git-wrench branch list"))

    repos = git_ops.find_repos(roots, max_depth=effective_depth)
    if not repos:
        print(YELLOW("No git repositories found."))
        return 0

    for repo in repos:
        base = git_ops.find_base_branch(repo.path, branches_order)
        branches = sorted(git_ops.local_branches(repo.path))

        print(f"\n{BOLD(str(repo.path))}" + (DIM(f"  (base: {base})") if base else ""))

        if not branches:
            print(DIM("  (no local branches)"))
            continue

        # Pre-collect changed files per branch so we can detect cross-branch conflicts.
        non_base = [b for b in branches if base is None or b != base]
        branch_files: dict[str, list[str]] = {}
        if base is not None:
            for b in non_base:
                branch_files[b] = git_ops.branch_changed_files(repo.path, b, base)

        # Count how many branches each file appears in.
        from collections import Counter

        file_branch_count: Counter[str] = Counter(f for files in branch_files.values() for f in files)

        for idx, branch in enumerate(branches, start=1):
            is_base = base and branch == base
            branch_label = DIM(CYAN(branch)) if is_base else CYAN(branch)
            print(f"  {DIM(str(idx) + '.')} {branch_label}")

            if is_base:
                print(DIM("      (base branch — skipped)"))
                continue

            if base is None:
                print(DIM("      (no base branch found — cannot diff)"))
                continue

            files = branch_files.get(branch, [])
            if files:
                for f in files:
                    label = YELLOW(f) if file_branch_count[f] > 1 else f
                    print(f"      {DIM('·')} {label}")
            else:
                print(DIM("      (no changed files)"))

    return 0


# ── rebase ────────────────────────────────────────────────────────────────────


def _rebase(args: list[str]) -> int:
    """Rebase local branches onto the configured base branch."""
    from git_wrench import config as cfg
    from git_wrench import git_ops

    override_path: Path | None = None
    use_workspace = False
    only_branch: str | None = None
    dry_run = False
    i = 0
    while i < len(args):
        if args[i] in ("--path", "-p") and i + 1 < len(args):
            override_path = Path(args[i + 1]).expanduser().resolve()
            i += 2
        elif args[i] == "--workspace":
            use_workspace = True
            i += 1
        elif args[i] == "--branch" and i + 1 < len(args):
            only_branch = args[i + 1]
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    conf = cfg.load()
    sync_cfg = conf.get("sync", {})
    rebase_cfg = conf.get("rebase", {})
    depth = int(sync_cfg.get("recurse_depth", 2))
    branches_order: list[str] = rebase_cfg.get("branches_order", ["develop", "main", "master"])

    roots, effective_depth = _resolve_roots(override_path, use_workspace, conf, depth)
    if not roots:
        print(RED("No workspace paths configured. Run 'git-wrench' interactively to add one."))
        return 1

    print(BOLD("git-wrench branch rebase"))
    if dry_run:
        print(DIM("  (dry run — no changes will be made)"))

    repos = git_ops.find_repos(roots, max_depth=effective_depth)
    if not repos:
        print(YELLOW("No git repositories found."))
        return 0

    global_err = 0

    for repo in repos:
        base = git_ops.find_base_branch(repo.path, branches_order)
        if base is None:
            print(DIM(f"\n  {repo.path}: no base branch found {branches_order}, skipping."))
            continue

        # Collect branches to rebase: all local branches except the base branches
        # themselves (and any other branches_order members).
        base_set = set(branches_order)
        if only_branch:
            if only_branch in base_set:
                print(YELLOW(f"\n  {repo.path}: '{only_branch}' is a base branch, skipping."))
                continue
            candidates = [only_branch]
        else:
            candidates = [b for b in git_ops.local_branches(repo.path) if b not in base_set]

        if not candidates:
            continue

        print(BOLD(f"\n  {repo.path}") + DIM(f"  (base: {base})"))

        ok = skipped = failed = 0
        for branch in candidates:
            label = f"    {CYAN(branch + ' '):.<55} "
            sys.stdout.write(label)
            sys.stdout.flush()

            if dry_run:
                print(DIM(f"would rebase onto {base}"))
                skipped += 1
                continue

            success, msg = git_ops.rebase_branch(repo.path, branch, base)
            if success:
                # "Already up to date." is not an error but worth distinguishing
                if "up to date" in msg.lower() or msg.strip() == "":
                    print(DIM("✓ up to date"))
                else:
                    print(GREEN("✓ " + msg.splitlines()[0]))
                ok += 1
            else:
                print(RED("✗ " + msg.splitlines()[0] if msg else "✗ failed"))
                failed += 1
                global_err += 1

        if not dry_run:
            summary = DIM(f"    {len(candidates)} branch(es) — {ok} ok, {skipped} skipped")
            if failed:
                summary += RED(f", {failed} failed")
            print(summary)

    return 0 if global_err == 0 else 1
