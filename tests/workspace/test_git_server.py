"""
CLI tests for:  git-wrench workspace <name> add-server / remove-server / list-server

Strategy
────────
* Each test gets a fresh XDG_CONFIG_HOME (via the `isolated_config` fixture)
  so it never touches the real user config.
* Three workspaces are created first (test-1, test-2, test-3).
* Servers are added via the CLI and then verified by reading the raw TOML
  directly from disk – no mocking, no internal imports, just the file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import read_raw_config, run, workspace_entries

# ── helpers ───────────────────────────────────────────────────────────────────


def _servers_for(xdg_dir: Path, workspace_name: str) -> list[dict]:
    """Return the raw server list for *workspace_name* from the on-disk config."""
    entries = workspace_entries(xdg_dir)
    for ws in entries:
        if ws["name"] == workspace_name:
            return ws.get("servers", [])
    return []


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def three_workspaces(isolated_config: Path) -> Path:
    """Create workspaces test-1, test-2, test-3 and return the xdg dir."""
    assert run(["workspace", "add", "test-1", "/tmp/ws1"]) == 0
    assert run(["workspace", "add", "test-2", "/tmp/ws2"]) == 0
    assert run(["workspace", "add", "test-3", "/tmp/ws3"]) == 0
    return isolated_config


# ── workspace creation sanity ─────────────────────────────────────────────────


def test_three_workspaces_are_created(three_workspaces: Path) -> None:
    names = [e["name"] for e in workspace_entries(three_workspaces)]
    assert "test-1" in names
    assert "test-2" in names
    assert "test-3" in names


# ── add-server ────────────────────────────────────────────────────────────────


def test_add_one_server_to_test1(three_workspaces: Path) -> None:
    rc = run(["workspace", "test-1", "add-server", "--type", "gitolite", "origin", "git@git.example.com"])
    assert rc == 0

    servers = _servers_for(three_workspaces, "test-1")
    assert len(servers) == 1
    assert servers[0]["server_name"] == "origin"
    assert servers[0]["server_type"] == "gitolite"
    assert servers[0]["server_url"] == "git@git.example.com"


def test_add_two_servers_to_test2(three_workspaces: Path) -> None:
    assert run(["workspace", "test-2", "add-server", "--type", "github", "gh", "https://github.com"]) == 0
    assert run(["workspace", "test-2", "add-server", "--type", "gitlab", "gl", "https://gitlab.example.com"]) == 0

    servers = _servers_for(three_workspaces, "test-2")
    assert len(servers) == 2

    by_name = {s["server_name"]: s for s in servers}

    # verify first server
    assert by_name["gh"]["server_type"] == "github"
    assert by_name["gh"]["server_url"] == "https://github.com"

    # verify second server
    assert by_name["gl"]["server_type"] == "gitlab"
    assert by_name["gl"]["server_url"] == "https://gitlab.example.com"


def test_add_three_servers_to_test3(three_workspaces: Path) -> None:
    assert run(["workspace", "test-3", "add-server", "--type", "gitolite", "internal", "git@internal.example.com"]) == 0
    assert run(["workspace", "test-3", "add-server", "--type", "github", "upstream", "https://github.com"]) == 0
    assert run(["workspace", "test-3", "add-server", "--type", "gitlab", "mirror", "https://gitlab.example.com"]) == 0

    servers = _servers_for(three_workspaces, "test-3")
    assert len(servers) == 3
    names = [s["server_name"] for s in servers]
    assert names == ["internal", "upstream", "mirror"]


# ── verify first / second server individually ─────────────────────────────────


def test_first_server_correct_after_two_adds(three_workspaces: Path) -> None:
    """After adding two servers, re-parse TOML and confirm the first entry."""
    assert run(["workspace", "test-1", "add-server", "--type", "gitolite", "primary", "git@primary.example.com"]) == 0
    assert run(["workspace", "test-1", "add-server", "--type", "github", "secondary", "https://github.com/org"]) == 0

    # read raw TOML – do not use any WorkspaceManager here
    raw = read_raw_config(three_workspaces)
    ws_list = raw["workspaces"]["list"]
    ws = next(w for w in ws_list if w["name"] == "test-1")
    servers = ws["servers"]

    # first server (index 0)
    assert servers[0]["server_name"] == "primary"
    assert servers[0]["server_type"] == "gitolite"
    assert servers[0]["server_url"] == "git@primary.example.com"

    # second server (index 1)
    assert servers[1]["server_name"] == "secondary"
    assert servers[1]["server_type"] == "github"
    assert servers[1]["server_url"] == "https://github.com/org"


# ── remove-server ─────────────────────────────────────────────────────────────


def test_remove_server(three_workspaces: Path) -> None:
    assert run(["workspace", "test-2", "add-server", "--type", "github", "to-remove", "https://github.com"]) == 0
    assert run(["workspace", "test-2", "add-server", "--type", "gitolite", "keeper", "git@keep.example.com"]) == 0

    # confirm both present before removal
    assert len(_servers_for(three_workspaces, "test-2")) == 2

    rc = run(["workspace", "test-2", "remove-server", "to-remove"])
    assert rc == 0

    servers = _servers_for(three_workspaces, "test-2")
    assert len(servers) == 1
    assert servers[0]["server_name"] == "keeper"


def test_remove_only_server_leaves_empty_list(three_workspaces: Path) -> None:
    assert run(["workspace", "test-1", "add-server", "--type", "gitlab", "solo", "https://gitlab.com"]) == 0
    assert run(["workspace", "test-1", "remove-server", "solo"]) == 0

    servers = _servers_for(three_workspaces, "test-1")
    assert servers == []


def test_remove_nonexistent_server_returns_error(three_workspaces: Path) -> None:
    rc = run(["workspace", "test-1", "remove-server", "does-not-exist"])
    assert rc != 0


# ── isolation: servers on one workspace don't affect others ───────────────────


def test_servers_are_isolated_per_workspace(three_workspaces: Path) -> None:
    assert run(["workspace", "test-1", "add-server", "--type", "github", "gh", "https://github.com"]) == 0

    assert _servers_for(three_workspaces, "test-2") == []
    assert _servers_for(three_workspaces, "test-3") == []


# ── list-server alias ─────────────────────────────────────────────────────────


def test_list_server_alias_works(three_workspaces: Path, capsys: pytest.CaptureFixture) -> None:
    assert run(["workspace", "test-1", "add-server", "--type", "gitolite", "orig", "git@x.example.com"]) == 0
    rc = run(["workspace", "test-1", "list-server"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "orig" in out
    assert "gitolite" in out


# ── duplicate server name is rejected ────────────────────────────────────────


def test_duplicate_server_name_rejected(three_workspaces: Path) -> None:
    assert run(["workspace", "test-1", "add-server", "--type", "github", "dup", "https://github.com"]) == 0
    rc = run(["workspace", "test-1", "add-server", "--type", "gitlab", "dup", "https://gitlab.com"])
    assert rc != 0


# ── invalid server type is rejected ──────────────────────────────────────────


def test_invalid_server_type_rejected(three_workspaces: Path) -> None:
    rc = run(["workspace", "test-1", "add-server", "--type", "svn", "bad", "https://svn.example.com"])
    assert rc != 0
