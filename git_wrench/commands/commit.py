"""
git-wrench commit — development and repository commit utilities.

Subcommands:
  split   Split a commit into smaller chunks.
          If the commit has multiple files, it splits the commit per file.
          If the commit has only one file, it splits the commit by hunks.

Usage:
  git-wrench commit split <commit>
"""

from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
from pathlib import Path

from git_wrench.commands._ansi import BOLD, CYAN, DIM, GREEN, RED, YELLOW
from git_wrench.registry import command


def run_git(args: list[str], cwd: Path, env: dict[str, str] | None = None, input_str: str | None = None) -> tuple[int, str, str]:
    """Run a git subcommand with custom environment and input."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    result = subprocess.run(  # nosec B603 B607
        args,
        cwd=cwd,
        env=full_env,
        input=input_str,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def split_diff_into_hunks(diff_text: str) -> list[str]:
    """Split a unified diff of a single file into separate hunk patches."""
    lines = diff_text.splitlines()
    header_lines = []
    hunks = []
    current_hunk = []

    for line in lines:
        if line.startswith("@@"):
            if current_hunk:
                hunks.append("\n".join(current_hunk) + "\n")
                current_hunk = []
            current_hunk.append(line)
        elif current_hunk:
            current_hunk.append(line)
        else:
            header_lines.append(line)

    if current_hunk:
        hunks.append("\n".join(current_hunk) + "\n")

    header = "\n".join(header_lines) + "\n"

    patches = []
    for hunk in hunks:
        patches.append(header + hunk)
    return patches


@command("commit", help="Commit and split utilities (split, …)", long_help=__doc__)
def run(args: list[str]) -> int:
    if not args or args[0] in ("-h", "--help"):
        print((__doc__ or "").strip())
        return 0

    subcmd = args[0]
    rest = args[1:]

    if subcmd == "split":
        return _split(rest)

    print(RED(f"git-wrench commit: unknown subcommand '{subcmd}'."), file=sys.stderr)
    print(DIM("Run 'git-wrench commit --help' for usage."), file=sys.stderr)
    return 1


def _split(args: list[str]) -> int:
    """Split a git commit into smaller chunks."""
    if not args or args[0] in ("-h", "--help"):
        print("Usage:\n  git-wrench commit split <commit>")
        return 0

    commit = args[0]
    cwd = Path.cwd()

    # 1. Verify we are in a git repository
    rc, _, _ = run_git(["git", "rev-parse", "--is-inside-work-tree"], cwd)
    if rc != 0:
        print(RED("Error: Not in a git repository."), file=sys.stderr)
        return 1

    # 2. Check if working directory is clean
    rc, status_out, _ = run_git(["git", "status", "--porcelain"], cwd)
    if status_out:
        print(RED("Error: Working directory has uncommitted changes. Please commit or stash them first."), file=sys.stderr)
        return 1

    # 3. Resolve commit to a full SHA
    rc, commit_sha, _ = run_git(["git", "rev-parse", "--verify", commit], cwd)
    if rc != 0:
        print(RED(f"Error: Commit '{commit}' could not be resolved."), file=sys.stderr)
        return 1

    # 4. Ensure commit is the current HEAD
    rc, head_sha, _ = run_git(["git", "rev-parse", "HEAD"], cwd)
    if rc == 0 and head_sha != commit_sha:
        msg = f"Error: Commit '{commit}' is not the current HEAD. Splitting is only supported for the current HEAD commit."
        print(RED(msg), file=sys.stderr)
        return 1

    # 5. Ensure commit has a parent
    rc, parent_sha, _ = run_git(["git", "rev-parse", "--verify", f"{commit_sha}^"], cwd)
    if rc != 0:
        msg = f"Error: Commit '{commit}' has no parent (it is a root commit). Splitting root commits is not supported."
        print(RED(msg), file=sys.stderr)
        return 1

    # 6. Retrieve commit details
    _, author_name, _ = run_git(["git", "log", "-1", "--format=%an", commit_sha], cwd)
    _, author_email, _ = run_git(["git", "log", "-1", "--format=%ae", commit_sha], cwd)
    _, author_date, _ = run_git(["git", "log", "-1", "--format=%aI", commit_sha], cwd)
    _, commit_message, _ = run_git(["git", "log", "-1", "--format=%B", commit_sha], cwd)

    # 7. Get files modified in the commit
    rc, files_out, _ = run_git(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha], cwd)
    if rc != 0:
        print(RED("Error: Could not retrieve modified files for the commit."), file=sys.stderr)
        return 1

    files = [line.strip() for line in files_out.splitlines() if line.strip()]
    if not files:
        print(YELLOW("No files modified in this commit. Nothing to split."))
        return 0

    print(BOLD(f"Splitting commit {CYAN(commit_sha[:8])} ({len(files)} file(s)) ..."))

    # 8. Reset HEAD to parent to begin staging chunks
    rc, _, err = run_git(["git", "reset", "--mixed", f"{commit_sha}^"], cwd)
    if rc != 0:
        print(RED(f"Error: Failed to reset to parent commit: {err}"), file=sys.stderr)
        return 1

    env = {
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_AUTHOR_DATE": author_date,
    }

    if len(files) > 1:
        # Case A: Split commit per file
        for f in files:
            print(f"  Staging file: {CYAN(f)}")
            rc, _, err = run_git(["git", "add", "--", f], cwd)
            if rc != 0:
                print(RED(f"Error staging file '{f}': {err}"), file=sys.stderr)
                return 1

            # Prepare message with "- $filename" suffix
            msg_lines = commit_message.splitlines()
            if msg_lines:
                msg_lines[0] = f"{msg_lines[0]} - {f}"
            else:
                msg_lines = [f"- {f}"]
            new_message = "\n".join(msg_lines)

            print(f"  Committing file: {CYAN(f)}")
            rc, _, err = run_git(["git", "commit", "-F", "-"], cwd, env=env, input_str=new_message)
            if rc != 0:
                print(RED(f"Error committing file '{f}': {err}"), file=sys.stderr)
                return 1
    else:
        # Case B: Only one file, split by hunk
        f = files[0]
        # Get diff of this file between parent and working tree with forced prefixes
        rc, diff_text, _ = run_git(["git", "diff", "--src-prefix=a/", "--dst-prefix=b/", "--", f], cwd)
        patches = split_diff_into_hunks(diff_text)

        if not patches:
            print(YELLOW(f"No hunks found for {f}. Staging and committing whole file as single chunk."))
            rc, _, err = run_git(["git", "add", "--", f], cwd)
            if rc != 0:
                print(RED(f"Error staging file '{f}': {err}"), file=sys.stderr)
                return 1

            msg_lines = commit_message.splitlines()
            suffix = " - [1/1]"
            if msg_lines:
                msg_lines[0] = f"{msg_lines[0]}{suffix}"
            else:
                msg_lines = [suffix]
            new_message = "\n".join(msg_lines)

            rc, _, err = run_git(["git", "commit", "-F", "-"], cwd, env=env, input_str=new_message)
            if rc != 0:
                print(RED(f"Error committing file '{f}': {err}"), file=sys.stderr)
                return 1
        else:
            chunks_count = len(patches)
            print(BOLD(f"Splitting single file {CYAN(f)} into {chunks_count} hunk(s) ..."))
            for idx, patch in enumerate(patches, start=1):
                print(f"  Staging hunk {idx}/{chunks_count} ...")
                rc, _, err = run_git(["git", "apply", "--cached", "-"], cwd, input_str=patch)
                if rc != 0:
                    print(RED(f"Error applying hunk patch {idx}: {err}"), file=sys.stderr)
                    return 1

                # Prepare message with "- [$idx/$chunks_count]" suffix
                msg_lines = commit_message.splitlines()
                suffix = f" - [{idx}/{chunks_count}]"
                if msg_lines:
                    msg_lines[0] = f"{msg_lines[0]}{suffix}"
                else:
                    msg_lines = [suffix]
                new_message = "\n".join(msg_lines)

                print(f"  Committing hunk {idx}/{chunks_count} ...")
                rc, _, err = run_git(["git", "commit", "-F", "-"], cwd, env=env, input_str=new_message)
                if rc != 0:
                    print(RED(f"Error committing hunk {idx}: {err}"), file=sys.stderr)
                    return 1

    print(GREEN("Commit split successfully!"))
    return 0
