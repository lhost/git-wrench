"""
git-wrench workspace — manage workspace definitions.

Usage:
  git-wrench workspace list
  git-wrench workspace add   <name> <path>
  git-wrench workspace rename <old-name> <new-name>
  git-wrench workspace remove <name>
"""

from __future__ import annotations

import sys

from git_wrench.registry import command
from git_wrench.commands._ansi import BOLD, CYAN, DIM, GREEN, RED, YELLOW


@command("workspace", help="Manage workspaces (add, rename, remove)")
def run(args: list[str]) -> int:
    from git_wrench.workspace import WorkspaceManager

    mgr = WorkspaceManager.load()

    if not args or args[0] in ("list", "ls"):
        return _list(mgr)

    sub, rest = args[0], args[1:]

    if sub == "add":
        return _add(mgr, rest)
    if sub in ("rename", "mv"):
        return _rename(mgr, rest)
    if sub in ("remove", "rm", "delete"):
        return _remove(mgr, rest)

    print(
        f"git-wrench workspace: unknown sub-command '{sub}'.\n"
        "Usage:  workspace list | add <name> <path> | rename <old> <new> | remove <name>",
        file=sys.stderr,
    )
    return 1


# ── sub-commands ──────────────────────────────────────────────────────────────


def _list(mgr) -> int:
    workspaces = mgr.all()
    if not workspaces:
        print(YELLOW("No workspaces configured."))
        print(DIM("  Add one with:  git-wrench workspace add <name> <path>"))
        return 0

    print(BOLD(f"  {'Name':<24}"), BOLD(f" {'Path'}"))
    print("  " + "─" * 60)
    for ws in workspaces:
        print(CYAN(f"  {ws.name:<24}"), f" {ws.path}")
    return 0


def _add(mgr, args: list[str]) -> int:
    if len(args) < 2:
        print("Usage:  git-wrench workspace add <name> <path>", file=sys.stderr)
        return 1
    name, path = args[0], args[1]
    try:
        ws = mgr.add(name, path)
        mgr.save()
        print(GREEN(f"Added workspace '{ws.name}' → {ws.path}"))
        return 0
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1


def _rename(mgr, args: list[str]) -> int:
    if len(args) < 2:
        print(
            "Usage:  git-wrench workspace rename <old-name> <new-name>", file=sys.stderr
        )
        return 1
    old, new = args[0], args[1]
    try:
        mgr.rename(old, new)
        mgr.save()
        print(GREEN(f"Renamed workspace '{old}' → '{new}'"))
        return 0
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1


def _remove(mgr, args: list[str]) -> int:
    if not args:
        print("Usage:  git-wrench workspace remove <name>", file=sys.stderr)
        return 1
    name = args[0]
    try:
        ws = mgr.remove(name)
        mgr.save()
        print(GREEN(f"Removed workspace '{ws.name}' ({ws.path})"))
        return 0
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1
