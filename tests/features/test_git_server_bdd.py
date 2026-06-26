"""
BDD tests for git server management.

Each call to scenario() binds one Gherkin scenario to a pytest test function.
Step definitions live in tests/features/conftest.py.
"""

from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenario

FEATURE = str(Path(__file__).parent / "git_server.feature")


@scenario(FEATURE, "Add a gitolite server to test-1")
def test_add_one_server_to_test1() -> None: ...


@scenario(FEATURE, "Add two servers to test-2")
def test_add_two_servers_to_test2() -> None: ...


@scenario(FEATURE, "Add three servers to test-3 in order")
def test_add_three_servers_to_test3() -> None: ...


@scenario(FEATURE, "Remove a server from a workspace")
def test_remove_server() -> None: ...


@scenario(FEATURE, "Removing the only server leaves an empty server list")
def test_remove_only_server_leaves_empty_list() -> None: ...


@scenario(FEATURE, "Removing a non-existent server returns an error")
def test_remove_nonexistent_server_returns_error() -> None: ...


@scenario(FEATURE, "Servers added to one workspace do not appear in others")
def test_servers_are_isolated_per_workspace() -> None: ...


@scenario(FEATURE, "list-server shows added server details")
def test_list_server_alias_works() -> None: ...


@scenario(FEATURE, "Duplicate server name in the same workspace is rejected")
def test_duplicate_server_name_rejected() -> None: ...


@scenario(FEATURE, "Invalid server type is rejected")
def test_invalid_server_type_rejected() -> None: ...
