"""
Shared pytest fixtures for git-wrench tests.
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import pytest
import tomli_w


@pytest.fixture()
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point XDG_CONFIG_HOME at a fresh tmp directory for the duration of the test.

    Returns the xdg base directory.  The config file lives at:
        <xdg>/git-wrench/config.toml

    A minimal *empty* config (no workspaces) is pre-written so that
    DEFAULT_CONFIG is never merged in — tests start from a truly blank slate.
    """
    xdg = tmp_path / "xdg"
    cfg_dir = xdg / "git-wrench"
    cfg_dir.mkdir(parents=True)

    # Write a minimal config with an empty workspace list so DEFAULT_CONFIG
    # is never used (config.load() merges defaults only when no file exists).
    with (cfg_dir / "config.toml").open("wb") as fh:
        tomli_w.dump({"workspaces": {"list": []}, "sync": {}}, fh)

    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    return xdg


def read_raw_config(xdg_dir: Path) -> dict:
    """Parse the config.toml written under *xdg_dir* and return its raw dict."""
    cfg_path = xdg_dir / "git-wrench" / "config.toml"
    with cfg_path.open("rb") as fh:
        return tomllib.load(fh)


def workspace_entries(xdg_dir: Path) -> list[dict]:
    """Return the raw workspace list from the on-disk config."""
    return read_raw_config(xdg_dir).get("workspaces", {}).get("list", [])


def run(argv: list[str]) -> int:
    """Invoke main.main() with *argv*, returning the exit code."""
    from main import main

    return main(argv)
