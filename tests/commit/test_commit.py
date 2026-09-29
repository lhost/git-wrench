"""
Tests for 'git-wrench commit split' command.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from git_wrench.commands.commit import split_diff_into_hunks


@pytest.fixture()
def temp_git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary git repository and make it the current working directory."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    # Init git
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    # Configure dummy user
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True, capture_output=True)
    # Set default branch
    subprocess.run(["git", "checkout", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)

    # Root commit (cannot split root commit)
    init_file = repo_dir / "init.txt"
    init_file.write_text("initial content\n")
    subprocess.run(["git", "add", "init.txt"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True, capture_output=True)

    monkeypatch.chdir(repo_dir)
    return repo_dir


def test_split_diff_into_hunks() -> None:
    """Test unified diff splitting into distinct hunk patches."""
    diff_text = (
        "diff --git a/file.txt b/file.txt\n"
        "index 123456..789abc 100644\n"
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,3 +1,4 @@\n"
        " line1\n"
        "+first hunk added\n"
        " line2\n"
        " line3\n"
        "@@ -10,3 +11,4 @@\n"
        " line10\n"
        "+second hunk added\n"
        " line11\n"
        " line12\n"
    )
    patches = split_diff_into_hunks(diff_text)
    assert len(patches) == 2
    assert "first hunk added" in patches[0]
    assert "second hunk added" not in patches[0]
    assert "second hunk added" in patches[1]
    assert "first hunk added" not in patches[1]


def test_split_multiple_files(temp_git_repo: Path) -> None:
    """Test splitting a commit with multiple files into one commit per file."""
    # Create multiple files and commit them
    f1 = temp_git_repo / "file1.txt"
    f2 = temp_git_repo / "file2.txt"
    f1.write_text("file 1 content\n")
    f2.write_text("file 2 content\n")

    subprocess.run(["git", "add", "file1.txt", "file2.txt"], cwd=temp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Add two files"], cwd=temp_git_repo, check=True, capture_output=True)

    # Run the split command
    from tests.conftest import run

    rc = run(["commit", "split", "HEAD"])
    assert rc == 0

    # Verify that we now have two new commits on top of the initial commit
    res = subprocess.run(
        ["git", "log", "--oneline", "-n", "3"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = res.stdout.strip().splitlines()
    assert len(lines) == 3  # Initial commit + 2 split commits

    messages = [line.split(" ", 1)[1] for line in lines[:2]]
    assert "Add two files - file1.txt" in messages or "Add two files - file2.txt" in messages


def test_split_single_file_multiple_hunks(temp_git_repo: Path) -> None:
    """Test splitting a commit with a single file containing multiple hunks."""
    # Create a multiline file and commit it
    f = temp_git_repo / "multiline.txt"
    lines = [f"line {i}\n" for i in range(1, 20)]
    f.write_text("".join(lines))
    subprocess.run(["git", "add", "multiline.txt"], cwd=temp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Add multiline file"], cwd=temp_git_repo, check=True, capture_output=True)

    # Modify the file in two separate places to create two disjoint hunks
    lines[2] = "line 3 modified\n"
    lines[15] = "line 16 modified\n"
    f.write_text("".join(lines))

    subprocess.run(["git", "add", "multiline.txt"], cwd=temp_git_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Modify multiple lines"], cwd=temp_git_repo, check=True, capture_output=True)

    # Run the split command
    from tests.conftest import run

    rc = run(["commit", "split", "HEAD"])
    assert rc == 0

    # Verify that we now have two commits with the expected suffixes
    res = subprocess.run(
        ["git", "log", "--oneline", "-n", "2"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    log_lines = res.stdout.strip().splitlines()
    assert "Modify multiple lines - [2/2]" in log_lines[0]
    assert "Modify multiple lines - [1/2]" in log_lines[1]
