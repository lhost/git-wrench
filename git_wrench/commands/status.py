"""
git-wrench status — show repo overview table.

Usage:
  git-wrench status [--path <dir>]
"""

from __future__ import annotations

from pathlib import Path

from git_wrench.commands._ansi import BOLD, CYAN, DIM, RED, YELLOW
from git_wrench.registry import command


@command("status", help="Show branch / ahead-behind / dirty state for all repos")
def run(args: list[str]) -> int:
    # Heavy imports deferred until command execution.
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
        print(RED("No workspace paths configured."))
        return 1

    depth = int(sync_cfg.get("recurse_depth", 2))

    repos = git_ops.find_repos(roots, max_depth=depth)
    if not repos:
        print(YELLOW("No git repositories found."))
        return 0

    print(BOLD(f"{'Repository':<50} {'Branch':<20} {'↑':<5} {'↓':<5} {'Dirty'}"))
    print("─" * 85)

    for repo in repos:
        git_ops.refresh_status(repo)
        dirty_flag = YELLOW("*") if repo.dirty else " "
        ahead_s = str(repo.ahead) if repo.ahead else DIM("0")
        behind_s = str(repo.behind) if repo.behind else DIM("0")
        branch_col = CYAN(repo.branch) if repo.branch not in ("?", "") else RED("?")
        print(f"  {str(repo.path):<48}  {branch_col:<20} {ahead_s:<5} {behind_s:<5} {dirty_flag}")

    return 0
