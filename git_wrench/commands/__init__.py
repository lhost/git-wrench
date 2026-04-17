"""
Command package for git-wrench.

Auto-discovery: importing this package registers all commands in the registry
by importing each sibling module that doesn't start with '_'.  This is the
only place where all command modules are touched — and it happens lazily,
only when dispatch() needs to know what commands exist (e.g. for --help).

For the hot path (git-wrench <known-command> …) the registry already has the
entry written by the @command decorator at module import time, so
auto-discovery is never triggered at all.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path


def _discover() -> None:
    """Import every public command module so their @command decorators fire."""
    pkg_path = str(Path(__file__).parent)
    pkg_name = __name__
    for finder, module_name, _ in pkgutil.iter_modules([pkg_path]):
        if not module_name.startswith("_"):
            importlib.import_module(f"{pkg_name}.{module_name}")
