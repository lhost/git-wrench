"""
Git repository discovery and operations.
"""

from __future__ import annotations

import subprocess  # nosec B404
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

# ── data model ────────────────────────────────────────────────────────────────


class RepoStatus(Enum):
    PENDING = auto()
    OK = auto()
    CHANGED = auto()  # local uncommitted changes
    CONFLICT = auto()  # merge conflict
    ERROR = auto()
    CLONED = auto()  # freshly cloned


@dataclass
class RepoInfo:
    path: Path
    branch: str = ""
    ahead: int = 0  # commits ahead of upstream
    behind: int = 0  # commits behind upstream
    dirty: bool = False  # has uncommitted changes
    status: RepoStatus = RepoStatus.PENDING
    message: str = ""  # last operation output or error


# ── discovery ─────────────────────────────────────────────────────────────────


def find_repos(roots: list[Path], max_depth: int = 2) -> list[RepoInfo]:
    """Walk *roots* up to *max_depth* subdirectory levels and return git repos.

    A directory that is itself a git repo is never descended into further
    (no nested repo detection needed).
    """
    repos: list[RepoInfo] = []
    seen: set[Path] = set()

    def _walk(directory: Path, depth: int) -> None:
        if not directory.is_dir():
            return
        git_dir = directory / ".git"
        if git_dir.exists():
            resolved = directory.resolve()
            if resolved not in seen:
                seen.add(resolved)
                repos.append(RepoInfo(path=directory))
            return  # don't recurse into sub-repos
        if depth == 0:
            return
        try:
            for child in sorted(directory.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    _walk(child, depth - 1)
        except PermissionError:
            pass

    for root in roots:
        _walk(root, max_depth)

    return repos


# ── low-level git helpers ─────────────────────────────────────────────────────


def _run(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run a git sub-command, return (returncode, stdout, stderr)."""
    result = subprocess.run(  # nosec B603 B607
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def refresh_status(repo: RepoInfo) -> None:
    """Populate *repo* with current branch, ahead/behind, and dirty flag."""
    # current branch
    rc, out, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo.path)
    repo.branch = out if rc == 0 else "?"

    # ahead / behind upstream
    rc, out, _ = _run(
        ["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"],
        repo.path,
    )
    if rc == 0:
        parts = out.split()
        if len(parts) == 2:
            repo.behind = int(parts[0])
            repo.ahead = int(parts[1])
    else:
        repo.behind = repo.ahead = 0

    # dirty working tree
    rc, out, _ = _run(["git", "status", "--porcelain"], repo.path)
    repo.dirty = bool(out)

    repo.status = RepoStatus.PENDING


# ── sync operation ────────────────────────────────────────────────────────────


def sync_repo(repo: RepoInfo, *, fetch_prune: bool = True, stash: bool = False) -> None:
    """Pull the latest changes for *repo*, updating ``repo.status`` and ``repo.message``."""

    # optionally stash local changes first
    if stash and repo.dirty:
        rc, _, err = _run(
            ["git", "stash", "push", "--include-untracked", "-m", "git-wrench auto-stash"],
            repo.path,
        )
        if rc != 0:
            repo.status = RepoStatus.ERROR
            repo.message = f"stash failed: {err}"
            return

    # fetch
    fetch_args = ["git", "fetch"]
    if fetch_prune:
        fetch_args.append("--prune")
    rc, _, err = _run(fetch_args, repo.path)
    if rc != 0:
        repo.status = RepoStatus.ERROR
        repo.message = f"fetch failed: {err}"
        return

    # fast-forward merge (pull --ff-only is safe and non-destructive)
    rc, out, err = _run(["git", "merge", "--ff-only", "@{u}"], repo.path)
    if rc == 0:
        repo.status = RepoStatus.OK
        repo.message = out or "Already up to date."
    else:
        # Could be diverged, or no upstream — not an error worth aborting on
        repo.status = RepoStatus.CHANGED if repo.dirty else RepoStatus.CONFLICT
        repo.message = err or out

    # refresh metadata
    refresh_status(repo)


# ── branch operations ────────────────────────────────────────────────────────


def gone_branches(repo_path: Path) -> list[str]:
    """Return local branch names whose upstream tracking ref is marked as gone.

    These are branches that once tracked a remote branch which has since been
    deleted (e.g. after a merged pull request was cleaned up on the server).
    ``git fetch --prune`` must have been run beforehand to update the remote
    tracking state; this function only reads what git already knows locally.
    """
    rc, out, _ = _run(
        ["git", "branch", "-vv"],
        repo_path,
    )
    if rc != 0 or not out:
        return []

    branches: list[str] = []
    for line in out.splitlines():
        # Strip the leading "* " (current branch marker) or "  "
        stripped = line.lstrip("* ").lstrip()
        # Branch name is the first token; the rest contains tracking info.
        # A gone upstream looks like: "branchname  <hash>  [origin/branchname: gone] ..."
        if ": gone]" in line:
            branch_name = stripped.split()[0]
            branches.append(branch_name)
    return branches


def local_branches(repo_path: Path) -> list[str]:
    """Return all local branch names, excluding HEAD."""
    rc, out, _ = _run(["git", "branch", "--format=%(refname:short)"], repo_path)
    if rc != 0 or not out:
        return []
    return [b for b in out.splitlines() if b and b != "HEAD"]


def branch_changed_files(repo_path: Path, branch: str, base: str) -> list[str]:
    """Return file paths changed in *branch* relative to *base*.

    Uses the three-dot diff (``base...branch``) so only commits unique to
    *branch* are considered, regardless of what has landed on *base* since.
    """
    rc, out, _ = _run(
        ["git", "diff", "--name-only", f"{base}...{branch}"],
        repo_path,
    )
    if rc != 0 or not out:
        return []
    return [f for f in out.splitlines() if f]


def find_base_branch(repo_path: Path, candidates: list[str]) -> str | None:
    """Return the first branch from *candidates* that exists locally in *repo_path*."""
    existing = set(local_branches(repo_path))
    for candidate in candidates:
        if candidate in existing:
            return candidate
    return None


def rebase_branch(repo_path: Path, branch: str, onto: str) -> tuple[bool, str]:
    """Rebase *branch* onto *onto* inside *repo_path*.

    Checks out *branch*, rebases it onto *onto*, then restores the original
    HEAD.  Returns ``(success, message)``.  On failure the rebase is aborted
    automatically so the repo is left in a clean state.
    """
    # remember current branch so we can restore it afterwards
    rc, original, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_path)
    original = original if rc == 0 else ""

    # check out the target branch
    rc, _, err = _run(["git", "checkout", branch], repo_path)
    if rc != 0:
        return False, f"checkout failed: {err}"

    # rebase
    rc, out, err = _run(["git", "rebase", onto], repo_path)
    if rc != 0:
        # abort so the repo is left clean
        _run(["git", "rebase", "--abort"], repo_path)
        # restore original branch
        if original and original != branch:
            _run(["git", "checkout", original], repo_path)
        return False, err or out

    # restore original branch
    if original and original != branch:
        _run(["git", "checkout", original], repo_path)

    return True, out or f"Rebased onto {onto}."


# ── clone operation ───────────────────────────────────────────────────────────


def clone_repo(
    clone_url: str,
    dest: Path,
    *,
    on_progress: Callable[[str], None] | None = None,
) -> RepoInfo:
    """Clone *clone_url* into *dest* and return a :class:`RepoInfo`.

    *dest* must not already exist.  Progress lines emitted by git are passed
    to *on_progress* if provided.

    Raises :class:`RuntimeError` on failure.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(  # nosec B603 B607
        ["git", "clone", "--", clone_url, str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    repo = RepoInfo(path=dest, status=RepoStatus.CLONED, message="Cloned.")
    if on_progress:
        for line in (result.stdout + result.stderr).splitlines():
            if line.strip():
                on_progress(line)
    return repo
