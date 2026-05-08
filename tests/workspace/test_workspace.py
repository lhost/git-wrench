"""
CLI tests for:  git-wrench workspace add / remove

Strategy
────────
* Each test gets a fresh XDG_CONFIG_HOME (via the `isolated_config` fixture)
  so it never touches the real user config.
* Assertions are made both against the CLI return code and against the raw
  TOML on disk, to confirm persistence end-to-end.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import read_raw_config, run, workspace_entries

# ── add workspace ─────────────────────────────────────────────────────────────


def test_add_workspace_returns_zero(isolated_config: Path) -> None:
    rc = run(["workspace", "add", "myws", "/tmp/myws"])
    assert rc == 0


def test_add_workspace_persisted_to_disk(isolated_config: Path) -> None:
    run(["workspace", "add", "myws", "/tmp/myws"])

    entries = workspace_entries(isolated_config)
    names = [e["name"] for e in entries]
    assert "myws" in names


def test_add_workspace_path_persisted(isolated_config: Path) -> None:
    run(["workspace", "add", "myws", "/tmp/myws"])

    entries = workspace_entries(isolated_config)
    ws = next(e for e in entries if e["name"] == "myws")
    assert ws["path"] == "/tmp/myws"


def test_add_multiple_workspaces(isolated_config: Path) -> None:
    run(["workspace", "add", "alpha", "/tmp/alpha"])
    run(["workspace", "add", "beta", "/tmp/beta"])
    run(["workspace", "add", "gamma", "/tmp/gamma"])

    entries = workspace_entries(isolated_config)
    names = [e["name"] for e in entries]
    assert "alpha" in names
    assert "beta" in names
    assert "gamma" in names


def test_add_duplicate_workspace_returns_error(isolated_config: Path) -> None:
    run(["workspace", "add", "dup", "/tmp/dup"])
    rc = run(["workspace", "add", "dup", "/tmp/dup2"])
    assert rc != 0


def test_add_duplicate_does_not_create_second_entry(isolated_config: Path) -> None:
    run(["workspace", "add", "dup", "/tmp/dup"])
    run(["workspace", "add", "dup", "/tmp/dup2"])

    entries = workspace_entries(isolated_config)
    matches = [e for e in entries if e["name"] == "dup"]
    assert len(matches) == 1


# ── remove workspace ──────────────────────────────────────────────────────────


def test_remove_workspace_returns_zero(isolated_config: Path) -> None:
    run(["workspace", "add", "torm", "/tmp/torm"])
    rc = run(["workspace", "remove", "torm"])
    assert rc == 0


def test_remove_workspace_absent_from_disk(isolated_config: Path) -> None:
    run(["workspace", "add", "torm", "/tmp/torm"])
    run(["workspace", "remove", "torm"])

    entries = workspace_entries(isolated_config)
    names = [e["name"] for e in entries]
    assert "torm" not in names


def test_remove_only_removes_target(isolated_config: Path) -> None:
    run(["workspace", "add", "keep", "/tmp/keep"])
    run(["workspace", "add", "gone", "/tmp/gone"])
    run(["workspace", "remove", "gone"])

    entries = workspace_entries(isolated_config)
    names = [e["name"] for e in entries]
    assert "keep" in names
    assert "gone" not in names


def test_remove_nonexistent_workspace_returns_error(isolated_config: Path) -> None:
    rc = run(["workspace", "remove", "no-such-workspace"])
    assert rc != 0


def test_remove_then_readd_same_name(isolated_config: Path) -> None:
    run(["workspace", "add", "cycle", "/tmp/v1"])
    run(["workspace", "remove", "cycle"])
    rc = run(["workspace", "add", "cycle", "/tmp/v2"])
    assert rc == 0

    entries = workspace_entries(isolated_config)
    ws = next(e for e in entries if e["name"] == "cycle")
    assert ws["path"] == "/tmp/v2"


# ── list workspace ────────────────────────────────────────────────────────────


def test_list_shows_added_workspace(isolated_config: Path, capsys: pytest.CaptureFixture) -> None:
    run(["workspace", "add", "visible", "/tmp/visible"])
    rc = run(["workspace", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "visible" in out


def test_list_does_not_show_removed_workspace(isolated_config: Path, capsys: pytest.CaptureFixture) -> None:
    run(["workspace", "add", "gone", "/tmp/gone"])
    run(["workspace", "remove", "gone"])
    capsys.readouterr()  # discard add/remove output
    run(["workspace", "list"])
    out = capsys.readouterr().out
    assert "gone" not in out


# ── raw config structure ──────────────────────────────────────────────────────


def test_raw_config_has_workspaces_key(isolated_config: Path) -> None:
    run(["workspace", "add", "raw", "/tmp/raw"])
    raw = read_raw_config(isolated_config)
    assert "workspaces" in raw
    assert "list" in raw["workspaces"]


def test_new_workspace_has_no_servers_key_by_default(isolated_config: Path) -> None:
    run(["workspace", "add", "clean", "/tmp/clean"])
    entries = workspace_entries(isolated_config)
    ws = next(e for e in entries if e["name"] == "clean")
    # servers key must be absent when no servers have been added
    assert "servers" not in ws
