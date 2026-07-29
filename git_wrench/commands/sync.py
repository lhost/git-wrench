"""
git-wrench sync — pull all repos in configured workspaces.

For workspaces that have git servers configured, the command also:
  1. Fetches the list of repositories from each configured server.
  2. Compares that list against what is already on disk.
  3. Clones any repository that is missing from disk.
  4. Pulls (fast-forward) every repository that already exists on disk.

Usage:
  git-wrench sync [--path <dir>]
"""

from __future__ import annotations

import sys
from pathlib import Path

from git_wrench.commands._ansi import BOLD, CYAN, DIM, GREEN, RED, YELLOW
from git_wrench.registry import command


@command("sync", help="Pull all repos in configured workspaces")
def run(args: list[str]) -> int:
    # Heavy imports stay inside the function — loaded only when this command runs.
    from git_wrench import config as cfg
    from git_wrench import git_ops
    from git_wrench import git_server as gs
    from git_wrench.workspace import WorkspaceManager

    conf = cfg.load()
    sync_cfg = conf.get("sync", {})

    override_path: Path | None = None
    i = 0
    while i < len(args):
        if args[i] in ("--path", "-p") and i + 1 < len(args):
            override_path = Path(args[i + 1]).expanduser().resolve()
            i += 2
        else:
            i += 1

    depth = int(sync_cfg.get("recurse_depth", 2))
    prune = bool(sync_cfg.get("fetch_prune", True))
    do_stash = bool(sync_cfg.get("stash_before_pull", False))

    print(BOLD("git-wrench sync"))

    # ── determine workspaces to process ───────────────────────────────────────

    if override_path:
        # --path mode: a plain directory scan, no server list comparison
        roots = [override_path]
        print(DIM(f"Searching for repos (depth={depth}) in:"))
        print(DIM(f"  {override_path}"))
        print()
        repos = git_ops.find_repos(roots, max_depth=depth)
        if not repos:
            print(YELLOW("No git repositories found."))
            return 0
        return _pull_repos(repos, prune=prune, stash=do_stash)

    mgr = WorkspaceManager.load()
    workspaces = mgr.all()

    if not workspaces:
        print(RED("No workspace paths configured. Run 'git-wrench' interactively to add one."))
        return 1

    global_err = 0

    for ws in workspaces:
        ws_path = ws.resolved_path
        print(BOLD(f"\nWorkspace: {ws.name}") + DIM(f"  ({ws_path})"))

        # paths that were just cloned — skip them in the pull phase
        just_cloned: set[Path] = set()

        # ── server-driven: clone missing repos ────────────────────────────────
        if ws.servers:
            for server in ws.servers:
                print(DIM(f"  Fetching repo list from {server.name} ({server.type})  {server.url} …"))
                try:
                    token = gs.resolve_token(server.token) if server.token else ""
                    adapter = gs.get_adapter(server.type, server.url, token=token)
                    remote_repos = adapter.list_repos()
                except Exception as exc:  # network/config errors must not abort everything
                    print(RED(f"  ✗ Could not reach server '{server.name}': {exc}"))
                    global_err += 1
                    continue

                print(DIM(f"    {len(remote_repos)} repos found on server."))

                cloned = cloned_err = 0
                for rrepo in remote_repos:
                    dest = ws_path / rrepo.name
                    if dest.exists():
                        continue  # already on disk — will be pulled below
                    sys.stdout.write(f"  {CYAN(rrepo.name):.<55} ")
                    sys.stdout.flush()
                    try:
                        git_ops.clone_repo(rrepo.clone_url, dest)
                        print(GREEN("✓ cloned"))
                        cloned += 1
                        just_cloned.add(dest.resolve())
                    except RuntimeError as exc:
                        print(RED(f"✗ clone failed: {exc}"))
                        cloned_err += 1
                        global_err += 1

                if cloned or cloned_err:
                    print(DIM(f"    Cloned: {cloned} new, {cloned_err} failed."))

        # ── pull repos on disk, skipping those just cloned ────────────────────
        print(DIM(f"  Searching for repos (depth={depth}) …"))
        repos = git_ops.find_repos([ws_path], max_depth=depth)
        if not repos:
            print(YELLOW("  No git repositories found on disk."))
            continue

        to_pull = [r for r in repos if r.path.resolve() not in just_cloned]
        err_count = _pull_repos(to_pull, prune=prune, stash=do_stash, indent="  ") if to_pull else 0
        global_err += err_count

    return 0 if global_err == 0 else 1


# ── helpers ───────────────────────────────────────────────────────────────────


def _pull_repos(
    repos: list,
    *,
    prune: bool,
    stash: bool,
    indent: str = "",
) -> int:
    """Pull each repo in *repos*, print results, return error count."""
    from git_wrench import git_ops

    ok_count = err_count = 0

    for repo in repos:
        sys.stdout.write(f"{indent}  {CYAN(str(repo.path) + ' '):.<60} ")
        sys.stdout.flush()

        git_ops.sync_repo(repo, fetch_prune=prune, stash=stash)

        if repo.status == git_ops.RepoStatus.OK:
            print(GREEN("✓ " + repo.message))
            ok_count += 1
        elif repo.status == git_ops.RepoStatus.ERROR:
            print(RED("✗ " + repo.message))
            err_count += 1
        else:
            print(YELLOW("~ " + repo.message))
            ok_count += 1

    summary = f"{indent}  {len(repos)} repos — {GREEN(str(ok_count) + ' ok')}"
    if err_count:
        summary += f", {RED(str(err_count) + ' errors')}"
    print(summary)

    return err_count
