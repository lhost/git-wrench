Feature: Workspace management
  As a user of git-wrench
  I want to manage named workspace directories
  So that I can organise my git repositories

  Background:
    Given a fresh configuration

  # ── add workspace ────────────────────────────────────────────────────────

  Scenario: Add a workspace returns exit code 0
    When I run "workspace add myws /tmp/myws"
    Then the exit code is 0

  Scenario: Added workspace is persisted to disk
    When I run "workspace add myws /tmp/myws"
    Then the workspace "myws" exists in config

  Scenario: Added workspace path is stored correctly
    When I run "workspace add myws /tmp/myws"
    Then the workspace "myws" has path "/tmp/myws"

  Scenario: Multiple workspaces can be added
    When I run "workspace add alpha /tmp/alpha"
    And I run "workspace add beta /tmp/beta"
    And I run "workspace add gamma /tmp/gamma"
    Then the workspace "alpha" exists in config
    And the workspace "beta" exists in config
    And the workspace "gamma" exists in config

  Scenario: Duplicate workspace name is rejected
    Given workspace "dup" exists at "/tmp/dup"
    When I run "workspace add dup /tmp/dup2"
    Then the exit code is non-zero

  Scenario: Duplicate add does not create a second entry
    Given workspace "dup" exists at "/tmp/dup"
    When I run "workspace add dup /tmp/dup2"
    Then the workspace "dup" appears exactly 1 time in config

  # ── remove workspace ──────────────────────────────────────────────────────

  Scenario: Remove a workspace returns exit code 0
    Given workspace "torm" exists at "/tmp/torm"
    When I run "workspace remove torm"
    Then the exit code is 0

  Scenario: Removed workspace is absent from disk
    Given workspace "torm" exists at "/tmp/torm"
    When I run "workspace remove torm"
    Then the workspace "torm" is absent from config

  Scenario: Remove only affects the target workspace
    Given workspace "keep" exists at "/tmp/keep"
    And workspace "gone" exists at "/tmp/gone"
    When I run "workspace remove gone"
    Then the workspace "keep" exists in config
    And the workspace "gone" is absent from config

  Scenario: Removing a non-existent workspace returns an error
    When I run "workspace remove no-such-workspace"
    Then the exit code is non-zero

  Scenario: Workspace can be re-added under the same name after removal
    Given workspace "cycle" exists at "/tmp/v1"
    When I run "workspace remove cycle"
    And I run "workspace add cycle /tmp/v2"
    Then the exit code is 0
    And the workspace "cycle" has path "/tmp/v2"

  # ── list workspace ────────────────────────────────────────────────────────

  Scenario: List output includes an added workspace
    Given workspace "visible" exists at "/tmp/visible"
    When I run "workspace list"
    Then the exit code is 0
    And the output contains "visible"

  Scenario: List output does not include a removed workspace
    Given workspace "gone" exists at "/tmp/gone"
    And I run "workspace remove gone"
    When I run "workspace list"
    Then the output does not contain "gone"

  # ── raw config structure ──────────────────────────────────────────────────

  Scenario: Config file has the workspaces key after adding a workspace
    When I run "workspace add raw /tmp/raw"
    Then the raw config has a "workspaces" key with a "list" sub-key

  Scenario: New workspace has no servers key by default
    When I run "workspace add clean /tmp/clean"
    Then the workspace "clean" has no servers key
