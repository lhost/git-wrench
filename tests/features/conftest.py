"""
Step definitions for git-wrench Gherkin (pytest-bdd) tests.

All step definitions live here; the thin test_*.py shims import scenarios from
the corresponding .feature files.  Fixtures from tests/conftest.py (e.g.
isolated_config) are re-used unchanged where possible.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
import tomli_w
from pytest_bdd import given, parsers, then, when

# ── shared state ──────────────────────────────────────────────────────────────
# pytest-bdd passes fixtures between steps via the fixture system.
# We store the last exit code and captured output in simple fixtures so that
# @when and @then steps can share them within a single scenario.


@pytest.fixture()
def last_rc() -> dict:
    """Mutable container for the most-recently observed exit code."""
    return {"value": None}


@pytest.fixture()
def last_output() -> dict:
    """Mutable container for the most-recently captured stdout."""
    return {"value": ""}


# ── background / given steps ──────────────────────────────────────────────────


@given("a fresh configuration", target_fixture="isolated_config")
def fresh_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Identical to the isolated_config fixture in tests/conftest.py."""
    xdg = tmp_path / "xdg"
    cfg_dir = xdg / "git-wrench"
    cfg_dir.mkdir(parents=True)
    with (cfg_dir / "config.toml").open("wb") as fh:
        tomli_w.dump({"workspaces": {"list": []}, "sync": {}}, fh)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    return xdg


@given(parsers.parse('workspace "{name}" exists at "{path}"'))
def workspace_exists(name: str, path: str, isolated_config: Path) -> None:
    """Pre-create a workspace via the CLI so subsequent steps start with it."""
    from tests.conftest import run

    assert run(["workspace", "add", name, path]) == 0


# ── when steps ────────────────────────────────────────────────────────────────


@when(parsers.parse('I run "{command}"'), target_fixture="last_rc")
def step_run(command: str, isolated_config: Path, capsys: pytest.CaptureFixture, last_output: dict) -> dict:
    """Run a git-wrench CLI command and store the exit code + stdout."""
    from tests.conftest import run

    rc = run(command.split())
    captured = capsys.readouterr()
    last_output["value"] = captured.out
    return {"value": rc}


# We need a separate @given variant of "I run" so Background steps work when
# a scenario also needs a @when "I run".  pytest-bdd distinguishes Given/When/Then
# at the step level, but a @given decorator makes the step usable in both contexts
# because pytest-bdd promotes Given/When/Then interchangeably for re-use.
@given(parsers.parse('I run "{command}"'), target_fixture="last_rc")
def given_run(command: str, isolated_config: Path, capsys: pytest.CaptureFixture, last_output: dict) -> dict:
    """Same as the @when variant — allows 'Given I run …' in feature files."""
    from tests.conftest import run

    rc = run(command.split())
    captured = capsys.readouterr()
    last_output["value"] = captured.out
    return {"value": rc}


# ── then steps — exit code ────────────────────────────────────────────────────


@then("the exit code is 0")
def exit_zero(last_rc: dict) -> None:
    assert last_rc["value"] == 0


@then("the exit code is non-zero")
def exit_nonzero(last_rc: dict) -> None:
    assert last_rc["value"] != 0


# ── then steps — output ───────────────────────────────────────────────────────


@then(parsers.parse('the output contains "{text}"'))
def output_contains(text: str, last_output: dict, capsys: pytest.CaptureFixture) -> None:
    # capsys may have additional output from the last run; merge both sources
    captured = capsys.readouterr()
    combined = last_output["value"] + captured.out
    assert text in combined


@then(parsers.parse('the output does not contain "{text}"'))
def output_not_contains(text: str, last_output: dict, capsys: pytest.CaptureFixture) -> None:
    captured = capsys.readouterr()
    combined = last_output["value"] + captured.out
    assert text not in combined


# ── helpers — raw config access ───────────────────────────────────────────────


def _read_config(xdg_dir: Path) -> dict:
    cfg_path = xdg_dir / "git-wrench" / "config.toml"
    with cfg_path.open("rb") as fh:
        return tomllib.load(fh)


def _workspace_entries(xdg_dir: Path) -> list[dict]:
    return _read_config(xdg_dir).get("workspaces", {}).get("list", [])


def _servers_for(xdg_dir: Path, workspace_name: str) -> list[dict]:
    for ws in _workspace_entries(xdg_dir):
        if ws["name"] == workspace_name:
            return ws.get("servers", [])
    return []


# ── then steps — workspace presence ──────────────────────────────────────────


@then(parsers.parse('the workspace "{name}" exists in config'))
def workspace_exists_in_config(name: str, isolated_config: Path) -> None:
    names = [e["name"] for e in _workspace_entries(isolated_config)]
    assert name in names


@then(parsers.parse('the workspace "{name}" is absent from config'))
def workspace_absent_from_config(name: str, isolated_config: Path) -> None:
    names = [e["name"] for e in _workspace_entries(isolated_config)]
    assert name not in names


@then(parsers.parse('the workspace "{name}" has path "{path}"'))
def workspace_has_path(name: str, path: str, isolated_config: Path) -> None:
    entries = _workspace_entries(isolated_config)
    ws = next((e for e in entries if e["name"] == name), None)
    assert ws is not None, f"Workspace '{name}' not found in config"
    assert ws["path"] == path


@then(parsers.parse('the workspace "{name}" appears exactly {count:d} time in config'))
def workspace_appears_n_times(name: str, count: int, isolated_config: Path) -> None:
    matches = [e for e in _workspace_entries(isolated_config) if e["name"] == name]
    assert len(matches) == count


@then(parsers.parse('the workspace "{name}" has no servers key'))
def workspace_no_servers_key(name: str, isolated_config: Path) -> None:
    entries = _workspace_entries(isolated_config)
    ws = next((e for e in entries if e["name"] == name), None)
    assert ws is not None
    assert "servers" not in ws


@then('the raw config has a "workspaces" key with a "list" sub-key')
def raw_config_structure(isolated_config: Path) -> None:
    raw = _read_config(isolated_config)
    assert "workspaces" in raw
    assert "list" in raw["workspaces"]


# ── then steps — server assertions ────────────────────────────────────────────


@then(parsers.parse('workspace "{name}" has exactly {count:d} server'))
@then(parsers.parse('workspace "{name}" has exactly {count:d} servers'))
def workspace_has_n_servers(name: str, count: int, isolated_config: Path) -> None:
    servers = _servers_for(isolated_config, name)
    assert len(servers) == count


@then(parsers.parse('workspace "{name}" has a server named "{server_name}" with type "{stype}" and url "{url}"'))
def workspace_has_server_full(name: str, server_name: str, stype: str, url: str, isolated_config: Path) -> None:
    servers = _servers_for(isolated_config, name)
    by_name = {s["server_name"]: s for s in servers}
    assert server_name in by_name, f"Server '{server_name}' not found in workspace '{name}'"
    assert by_name[server_name]["server_type"] == stype
    assert by_name[server_name]["server_url"] == url


@then(parsers.parse('workspace "{name}" has a server named "{server_name}"'))
def workspace_has_server_by_name(name: str, server_name: str, isolated_config: Path) -> None:
    servers = _servers_for(isolated_config, name)
    names = [s["server_name"] for s in servers]
    assert server_name in names


@then(parsers.parse('workspace "{name}" server order is "{s1}", "{s2}", "{s3}"'))
def workspace_server_order(name: str, s1: str, s2: str, s3: str, isolated_config: Path) -> None:
    servers = _servers_for(isolated_config, name)
    names = [s["server_name"] for s in servers]
    assert names == [s1, s2, s3]
