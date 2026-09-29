"""
git-wrench split — Split a git commit into smaller chunks.

This is an alias for 'git-wrench commit split'.

If the commit consists of multiple files, it splits the commit per file.
If only one file is in commit, it splits by hunks.

Options:
  --help         Show this help and exit

Usage:
  git-wrench split <commit>
"""

from __future__ import annotations

from git_wrench.registry import command


@command("split", help="Alias for 'git-wrench commit split'", long_help=__doc__)
def run(args: list[str]) -> int:
    from git_wrench.commands.commit import _split

    return _split(args)
