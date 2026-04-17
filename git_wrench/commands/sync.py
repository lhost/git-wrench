"""
git-wrench sync — pull all repos in configured workspaces.

Usage:
  git-wrench sync [--path <dir>]
"""

from __future__ import annotations

import sys
from pathlib import Path

from git_wrench.registry import command
from git_wrench.commands._ansi import BOLD, CYAN, DIM, GREEN, RED, YELLOW


@command("sync", help="Pull all repos in configured workspaces")
def run(args: list[str]) -> int:
    # Heavy imports stay inside the function — loaded only when this command runs.
    from git_wrench import config as cfg
    from git_wrench import git_ops

    conf = cfg.load()
    sync_cfg = conf.get("sync", {})

    override_path: Path | None = None
    i = 0
    while i < len(args):
        if args[i] in ("--path", "-p") and i + 1 < len(args):
            override_path = Path(args[i + 1]).expanduser().resolve()
            i += 2
        else:
            i += 1

    roots = [override_path] if override_path else cfg.workspace_paths(conf)

    if not roots:
        print(
            RED(
                "No workspace paths configured. Run 'git-wrench' interactively to add one."
            )
        )
        return 1

    depth = int(sync_cfg.get("recurse_depth", 2))
    prune = bool(sync_cfg.get("fetch_prune", True))
    do_stash = bool(sync_cfg.get("stash_before_pull", False))

    print(BOLD("git-wrench sync"))
    print(DIM(f"Searching for repos (depth={depth}) in:"))
    for root in roots:
        print(DIM(f"  {root}"))
    print()

    repos = git_ops.find_repos(roots, max_depth=depth)
    if not repos:
        print(YELLOW("No git repositories found."))
        return 0

    ok_count = err_count = 0

    for repo in repos:
        sys.stdout.write(f"  {CYAN(str(repo.path)):.<60} ")
        sys.stdout.flush()

        git_ops.sync_repo(repo, fetch_prune=prune, stash=do_stash)

        if repo.status == git_ops.RepoStatus.OK:
            print(GREEN("✓ " + repo.message))
            ok_count += 1
        elif repo.status == git_ops.RepoStatus.ERROR:
            print(RED("✗ " + repo.message))
            err_count += 1
        else:
            print(YELLOW("~ " + repo.message))
            ok_count += 1

    print()
    summary = f"{len(repos)} repos — {GREEN(str(ok_count) + ' ok')}"
    if err_count:
        summary += f", {RED(str(err_count) + ' errors')}"
    print(BOLD(summary))

    return 0 if err_count == 0 else 1
