"""
git-wrench branch — local branch management utilities.

Subcommands:
  gone   Delete local branches whose remote tracking ref has been removed.
         Runs 'git fetch --prune' first to refresh remote tracking state,
         then lists branches marked as '[gone]' and prompts before deletion.

Options (gone):
  --path <dir>   Scan a specific directory instead of configured workspaces
  --force        Delete branches with 'git branch -D' (unmerged branches too)
  --yes          Skip confirmation prompt and delete immediately

Usage:
  git-wrench branch gone
  git-wrench branch gone --path ~/my-workspace
  git-wrench branch gone --force
  git-wrench branch gone --yes
"""

from __future__ import annotations

import sys
from pathlib import Path

from git_wrench.commands._ansi import BOLD, CYAN, DIM, GREEN, RED, YELLOW
from git_wrench.registry import command


@command("branch", help="Local branch management (gone, …)", long_help=__doc__)
def run(args: list[str]) -> int:
    if not args or args[0] in ("-h", "--help"):
        print((__doc__ or "").strip())
        return 0

    subcmd, rest = args[0], args[1:]

    if subcmd == "gone":
        return _gone(rest)

    print(RED(f"git-wrench branch: unknown subcommand '{subcmd}'."), file=sys.stderr)
    print(DIM("Run 'git-wrench branch --help' for usage."), file=sys.stderr)
    return 1


# ── gone ──────────────────────────────────────────────────────────────────────


def _gone(args: list[str]) -> int:
    """Remove local branches whose upstream tracking ref is gone."""
    from git_wrench import config as cfg
    from git_wrench import git_ops

    override_path: Path | None = None
    force = False
    yes = False
    i = 0
    while i < len(args):
        if args[i] in ("--path", "-p") and i + 1 < len(args):
            override_path = Path(args[i + 1]).expanduser().resolve()
            i += 2
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

    roots = [override_path] if override_path else cfg.workspace_paths(conf)
    if not roots:
        print(RED("No workspace paths configured. Run 'git-wrench' interactively to add one."))
        return 1

    print(BOLD("git-wrench branch gone"))

    repos = git_ops.find_repos(roots, max_depth=depth)
    if not repos:
        print(YELLOW("No git repositories found."))
        return 0

    global_err = 0

    for repo in repos:
        # Fetch + prune so remote tracking state is up to date.
        sys.stdout.write(f"  {CYAN(str(repo.path)):.<60} fetching… ")
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
