Feature: Git server management
  As a user of git-wrench
  I want to associate git servers with workspaces
  So that git-wrench can clone and sync repositories from those servers

  Background:
    Given a fresh configuration
    And workspace "test-1" exists at "/tmp/ws1"
    And workspace "test-2" exists at "/tmp/ws2"
    And workspace "test-3" exists at "/tmp/ws3"

  # ── add-server ────────────────────────────────────────────────────────────

  Scenario: Add a gitolite server to test-1
    When I run "workspace test-1 add-server --type gitolite origin git@git.example.com"
    Then the exit code is 0
    And workspace "test-1" has exactly 1 server
    And workspace "test-1" has a server named "origin" with type "gitolite" and url "git@git.example.com"

  Scenario: Add two servers to test-2
    When I run "workspace test-2 add-server --type github gh https://github.com"
    And I run "workspace test-2 add-server --type gitlab gl https://gitlab.example.com"
    Then workspace "test-2" has exactly 2 servers
    And workspace "test-2" has a server named "gh" with type "github" and url "https://github.com"
    And workspace "test-2" has a server named "gl" with type "gitlab" and url "https://gitlab.example.com"

  Scenario: Add three servers to test-3 in order
    When I run "workspace test-3 add-server --type gitolite internal git@internal.example.com"
    And I run "workspace test-3 add-server --type github upstream https://github.com"
    And I run "workspace test-3 add-server --type gitlab mirror https://gitlab.example.com"
    Then workspace "test-3" has exactly 3 servers
    And workspace "test-3" server order is "internal", "upstream", "mirror"

  # ── remove-server ─────────────────────────────────────────────────────────

  Scenario: Remove a server from a workspace
    Given I run "workspace test-2 add-server --type github to-remove https://github.com"
    And I run "workspace test-2 add-server --type gitolite keeper git@keep.example.com"
    When I run "workspace test-2 remove-server to-remove"
    Then the exit code is 0
    And workspace "test-2" has exactly 1 server
    And workspace "test-2" has a server named "keeper"

  Scenario: Removing the only server leaves an empty server list
    Given I run "workspace test-1 add-server --type gitlab solo https://gitlab.com"
    When I run "workspace test-1 remove-server solo"
    Then the exit code is 0
    And workspace "test-1" has exactly 0 servers

  Scenario: Removing a non-existent server returns an error
    When I run "workspace test-1 remove-server does-not-exist"
    Then the exit code is non-zero

  # ── isolation ─────────────────────────────────────────────────────────────

  Scenario: Servers added to one workspace do not appear in others
    When I run "workspace test-1 add-server --type github gh https://github.com"
    Then workspace "test-2" has exactly 0 servers
    And workspace "test-3" has exactly 0 servers

  # ── list-server ───────────────────────────────────────────────────────────

  Scenario: list-server shows added server details
    Given I run "workspace test-1 add-server --type gitolite orig git@x.example.com"
    When I run "workspace test-1 list-server"
    Then the exit code is 0
    And the output contains "orig"
    And the output contains "gitolite"

  # ── duplicate / invalid validation ────────────────────────────────────────

  Scenario: Duplicate server name in the same workspace is rejected
    Given I run "workspace test-1 add-server --type github dup https://github.com"
    When I run "workspace test-1 add-server --type gitlab dup https://gitlab.com"
    Then the exit code is non-zero

  Scenario: Invalid server type is rejected
    When I run "workspace test-1 add-server --type svn bad https://svn.example.com"
    Then the exit code is non-zero
