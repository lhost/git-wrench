"""
Command registry for git-wrench.

Design goals
────────────
* Zero import cost at startup — command modules are never imported until the
  matching command is actually invoked (lazy importlib.import_module).
* Decorator-based registration: each command module calls @command(...) at
  module level.  The decorator stores only lightweight metadata (strings) in
  the registry dict, not the function itself.
* Single source of truth for the help text shown by --help.

Usage (in a command module)
───────────────────────────
    from git_wrench.registry import command

    @command("sync", help="Pull all repos in configured workspaces")
    def run(args: list[str]) -> int:
        ...
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(slots=True)
class _Entry:
    module: str  # fully-qualified module path, e.g. "git_wrench.commands.sync"
    attr: str  # function name inside that module
    help: str  # one-line description shown in --help
    long_help: str  # multi-line help shown by --help <command>


# Global registry: command name → _Entry
_REGISTRY: dict[str, _Entry] = {}


def command(name: str, *, help: str = "", long_help: str | None = None) -> Callable:
    """Decorator that registers a command function without importing the module eagerly.

    The decorated function is returned unchanged; only its location is recorded.
    """

    def _decorator(fn: Callable) -> Callable:
        module = fn.__module__
        _REGISTRY[name] = _Entry(module=module, attr=fn.__name__, help=help, long_help=long_help or "")
        return fn

    return _decorator


# ── public API ────────────────────────────────────────────────────────────────


def names() -> list[str]:
    """Return sorted list of registered command names."""
    return sorted(_REGISTRY)


def help_text(name: str) -> str:
    """Return the one-line help string for a command, or '' if unknown."""
    entry = _REGISTRY.get(name)
    return entry.help if entry else ""


def long_help_text(name: str) -> str:
    """Return the long (multi-line) help string for a command, or '' if unknown."""
    entry = _REGISTRY.get(name)
    return entry.long_help if entry else ""


def dispatch(name: str, args: list[str]) -> int | None:
    """Import the command module on demand and call its handler.

    Returns the integer exit code, or None if the command is not registered.
    """
    entry = _REGISTRY.get(name)
    if entry is None:
        return None
    mod = importlib.import_module(entry.module)
    fn: Callable[[list[str]], int] = getattr(mod, entry.attr)
    return fn(args)
