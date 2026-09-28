"""
git-wrench rebase — Rebase local branches onto the configured base branch.

This is an alias for 'git-wrench branch rebase'.
"""

from __future__ import annotations

from git_wrench.registry import command


@command("rebase", help="Alias for 'git-wrench branch rebase'", long_help=__doc__)
def run(args: list[str]) -> int:
    from git_wrench.commands.branch import _rebase

    return _rebase(args)
