"""
Configuration management for git-wrench.

Config file location (XDG-compliant):
  $XDG_CONFIG_HOME/git-wrench/config.toml
  ~/.config/git-wrench/config.toml  (fallback)

Example config.toml (~/.config/git-wrench/config.toml):
  [workspaces]
  list = [
      { name = "personal", path = "~/projects" },
      { name = "work",     path = "~/work" },
  ]

  [sync]
  recurse_depth = 2
  fetch_prune = true
  stash_before_pull = false
"""

from __future__ import annotations

import os
import tomllib
import tomli_w
from pathlib import Path
from typing import Any


# ── defaults ──────────────────────────────────────────────────────────────────

DEFAULT_CONFIG: dict[str, Any] = {
    "workspaces": {
        "list": [
            {"name": "projects", "path": str(Path.home() / "projects")},
        ],
    },
    "sync": {
        "recurse_depth": 2,
        "fetch_prune": True,
        "stash_before_pull": False,
    },
}


# ── helpers ───────────────────────────────────────────────────────────────────


def config_path() -> Path:
    """Return the path to config.toml, honouring $XDG_CONFIG_HOME."""
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "git-wrench" / "config.toml"


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into a copy of *base*."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


# ── public API ────────────────────────────────────────────────────────────────


def load() -> dict[str, Any]:
    """Load config from disk, merging with defaults.  Never raises."""
    path = config_path()
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with path.open("rb") as fh:
            on_disk = tomllib.load(fh)
        return _deep_merge(DEFAULT_CONFIG, on_disk)
    except Exception:
        return dict(DEFAULT_CONFIG)


def save(cfg: dict[str, Any]) -> None:
    """Persist *cfg* to disk, creating the directory if needed."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        tomli_w.dump(cfg, fh)


def workspace_list(conf: dict[str, Any]) -> list[dict[str, str]]:
    """Return raw workspace entries as {name, path} dicts.

    Internal helper used by WorkspaceManager.  Prefer WorkspaceManager for
    all higher-level workspace operations.
    """
    ws = conf.get("workspaces", {})
    entries = ws.get("list", [])
    # backward-compat: old format had paths = ["~/..."]
    if not entries and "paths" in ws:
        entries = [{"name": Path(p).name, "path": p} for p in ws["paths"]]
    return entries


def workspace_paths(conf: dict[str, Any]) -> list[Path]:
    """Return resolved workspace paths.  Prefer WorkspaceManager.paths()."""
    return [Path(e["path"]).expanduser().resolve() for e in workspace_list(conf)]
