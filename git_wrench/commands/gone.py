"""
git-wrench gone — Remove local branches whose upstream tracking ref is gone.

This is an alias for 'git-wrench branch gone'.
"""

from __future__ import annotations

from git_wrench.registry import command


@command("gone", help="Alias for 'git-wrench branch gone'", long_help=__doc__)
def run(args: list[str]) -> int:
    from git_wrench.commands.branch import _gone

    return _gone(args)
