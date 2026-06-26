"""
BDD tests for workspace management.

Each call to scenario() binds one Gherkin scenario to a pytest test function.
Step definitions live in tests/features/conftest.py.
"""

from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenario

FEATURE = str(Path(__file__).parent / "workspace.feature")


@scenario(FEATURE, "Add a workspace returns exit code 0")
def test_add_workspace_returns_zero() -> None: ...


@scenario(FEATURE, "Added workspace is persisted to disk")
def test_add_workspace_persisted_to_disk() -> None: ...


@scenario(FEATURE, "Added workspace path is stored correctly")
def test_add_workspace_path_persisted() -> None: ...


@scenario(FEATURE, "Multiple workspaces can be added")
def test_add_multiple_workspaces() -> None: ...


@scenario(FEATURE, "Duplicate workspace name is rejected")
def test_add_duplicate_workspace_returns_error() -> None: ...


@scenario(FEATURE, "Duplicate add does not create a second entry")
def test_add_duplicate_does_not_create_second_entry() -> None: ...


@scenario(FEATURE, "Remove a workspace returns exit code 0")
def test_remove_workspace_returns_zero() -> None: ...


@scenario(FEATURE, "Removed workspace is absent from disk")
def test_remove_workspace_absent_from_disk() -> None: ...


@scenario(FEATURE, "Remove only affects the target workspace")
def test_remove_only_removes_target() -> None: ...


@scenario(FEATURE, "Removing a non-existent workspace returns an error")
def test_remove_nonexistent_workspace_returns_error() -> None: ...


@scenario(FEATURE, "Workspace can be re-added under the same name after removal")
def test_remove_then_readd_same_name() -> None: ...


@scenario(FEATURE, "List output includes an added workspace")
def test_list_shows_added_workspace() -> None: ...


@scenario(FEATURE, "List output does not include a removed workspace")
def test_list_does_not_show_removed_workspace() -> None: ...


@scenario(FEATURE, "Config file has the workspaces key after adding a workspace")
def test_raw_config_has_workspaces_key() -> None: ...


@scenario(FEATURE, "New workspace has no servers key by default")
def test_new_workspace_has_no_servers_key_by_default() -> None: ...
