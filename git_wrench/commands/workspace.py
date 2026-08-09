"""
git-wrench workspace — manage workspace definitions.

Usage:
  git-wrench workspace list
  git-wrench workspace add   <name> <path>
  git-wrench workspace rename <old-name> <new-name>
  git-wrench workspace remove <name>
  git-wrench workspace <name> list-servers
  git-wrench workspace <name> add-server --type <type> [--token <path>] <server-name> <url>
  git-wrench workspace <name> remove-server <server-name>
  git-wrench workspace <name> add-token <server-name>
"""

from __future__ import annotations

import getpass
import subprocess
import sys
from pathlib import Path

from git_wrench.commands._ansi import BOLD, CYAN, DIM, GREEN, RED, YELLOW
from git_wrench.registry import command


@command("workspace", help="Manage workspaces (add, rename, remove, add-server…)", long_help=__doc__)
def run(args: list[str]) -> int:
    from git_wrench.workspace import WorkspaceManager

    mgr = WorkspaceManager.load()

    if not args or args[0] in ("list", "ls"):
        return _list(mgr)

    sub, rest = args[0], args[1:]

    if sub == "add":
        return _add(mgr, rest)
    if sub in ("rename", "mv"):
        return _rename(mgr, rest)
    if sub in ("remove", "rm", "delete"):
        return _remove(mgr, rest)

    # workspace <name> <server-sub-command> …
    workspace_name = sub
    if rest:
        server_sub = rest[0]
        server_args = rest[1:]
        if server_sub in ("add-server",):
            return _add_server(mgr, workspace_name, server_args)
        if server_sub in ("remove-server", "rm-server", "delete-server"):
            return _remove_server(mgr, workspace_name, server_args)
        if server_sub in ("list-servers", "list-server", "ls-servers", "ls-server"):
            return _list_servers(mgr, workspace_name)
        if server_sub in ("add-token",):
            return _add_token(mgr, workspace_name, server_args)

    print(
        f"git-wrench workspace: unknown sub-command '{sub}'.\n"
        "Usage:  workspace list | add <name> <path> | rename <old> <new> | remove <name>\n"
        "        workspace <name> list-servers\n"
        "        workspace <name> add-server --type <type> [--token <path>] <server-name> <url>\n"
        "        workspace <name> remove-server <server-name>\n"
        "        workspace <name> add-token <server-name>",
        file=sys.stderr,
    )
    return 1


# ── sub-commands ──────────────────────────────────────────────────────────────


def _list(mgr) -> int:
    workspaces = mgr.all()
    if not workspaces:
        print(YELLOW("No workspaces configured."))
        print(DIM("  Add one with:  git-wrench workspace add <name> <path>"))
        return 0

    print(BOLD(f"  {'Name':<24}"), BOLD(f" {'Path'}"))
    print("  " + "─" * 60)
    for ws in workspaces:
        print(CYAN(f"  {ws.name:<24}"), f" {ws.path}")
    return 0


def _add(mgr, args: list[str]) -> int:
    if len(args) < 2:
        print("Usage:  git-wrench workspace add <name> <path>", file=sys.stderr)
        return 1
    name, path = args[0], args[1]
    try:
        ws = mgr.add(name, path)
        mgr.save()
        print(GREEN(f"Added workspace '{ws.name}' → {ws.path}"))
        return 0
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1


def _rename(mgr, args: list[str]) -> int:
    if len(args) < 2:
        print("Usage:  git-wrench workspace rename <old-name> <new-name>", file=sys.stderr)
        return 1
    old, new = args[0], args[1]
    try:
        mgr.rename(old, new)
        mgr.save()
        print(GREEN(f"Renamed workspace '{old}' → '{new}'"))
        return 0
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1


def _remove(mgr, args: list[str]) -> int:
    if not args:
        print("Usage:  git-wrench workspace remove <name>", file=sys.stderr)
        return 1
    name = args[0]
    try:
        ws = mgr.remove(name)
        mgr.save()
        print(GREEN(f"Removed workspace '{ws.name}' ({ws.path})"))
        return 0
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1


# ── server sub-commands ───────────────────────────────────────────────────────


def _list_servers(mgr, workspace_name: str) -> int:
    try:
        servers = mgr.list_servers(workspace_name)
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1

    if not servers:
        print(YELLOW(f"No servers configured for workspace '{workspace_name}'."))
        print(DIM(f"  Add one with:  git-wrench workspace {workspace_name} add-server --type <type> <name> <url>"))
        return 0

    print(BOLD(f"  {'Name':<20}"), BOLD(f"{'Type':<12}"), BOLD(f"{'URL':<40}"), BOLD("Token"))
    print("  " + "─" * 80)
    for s in servers:
        token_hint = s.token if s.token else ""
        print(CYAN(f"  {s.name:<20}"), f"{s.type:<12}", f"{s.url:<40}", DIM(token_hint))
    return 0


def _add_server(mgr, workspace_name: str, args: list[str]) -> int:
    """Parse:  [--type <type>] [--token <path>] <server-name> <url>"""
    server_type = "github"
    token_path = ""
    rest = list(args)

    # consume --type and --token flags
    while len(rest) >= 2 and rest[0].startswith("--"):
        if rest[0] == "--type":
            server_type = rest[1]
            rest = rest[2:]
        elif rest[0] == "--token":
            token_path = rest[1]
            rest = rest[2:]
        else:
            break

    if len(rest) < 2:
        print(
            f"Usage:  git-wrench workspace {workspace_name} add-server --type <type> [--token <path>] <server-name> <url>",
            file=sys.stderr,
        )
        return 1

    server_name, server_url = rest[0], rest[1]
    try:
        server = mgr.add_server(workspace_name, server_type, server_name, server_url, token=token_path)
        mgr.save()
        msg = f"Added server '{server.name}' ({server.type}) → {server.url} to workspace '{workspace_name}'"
        if server.token:
            msg += f"\n  Token: {server.token}"
        print(GREEN(msg))
        return 0
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1


def _remove_server(mgr, workspace_name: str, args: list[str]) -> int:
    if not args:
        print(
            f"Usage:  git-wrench workspace {workspace_name} remove-server <server-name>",
            file=sys.stderr,
        )
        return 1
    server_name = args[0]
    try:
        server = mgr.remove_server(workspace_name, server_name)
        mgr.save()
        print(GREEN(f"Removed server '{server.name}' from workspace '{workspace_name}'"))
        return 0
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1


def _add_token(mgr, workspace_name: str, args: list[str]) -> int:
    """Interactively encrypt an API token with GPG and store the path in config.

    Prompts for the token (hidden input), encrypts it to an ASCII-armoured file
    using the user's default GPG key, writes the file to the git-wrench config
    directory, and saves the path back into the server entry.

    Default output path:  ~/.config/git-wrench/<workspace>-<server>-token.asc
    """
    if not args:
        print(
            f"Usage:  git-wrench workspace {workspace_name} add-token <server-name>",
            file=sys.stderr,
        )
        return 1

    server_name = args[0]

    # Verify the server exists before asking for input.
    try:
        servers = mgr.list_servers(workspace_name)
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1
    if not any(s.name == server_name for s in servers):
        print(RED(f"Server '{server_name}' not found in workspace '{workspace_name}'."), file=sys.stderr)
        return 1

    # Prompt for the token (no echo).
    try:
        token = getpass.getpass(f"Token for server '{server_name}': ")
    except KeyboardInterrupt, EOFError:
        print("\nAborted.", file=sys.stderr)
        return 1
    if not token.strip():
        print(RED("Token must not be empty."), file=sys.stderr)
        return 1

    # Determine output file path.
    from git_wrench import config as cfg

    token_file = Path(cfg.config_path().parent) / f"{workspace_name}-{server_name}-token.asc"

    # Encrypt with GPG (ASCII-armoured, default recipient = own key via --default-recipient-self).
    try:
        result = subprocess.run(  # nosec B603 B607
            ["gpg", "--quiet", "--batch", "--armor", "--encrypt", "--default-recipient-self", "--output", str(token_file)],
            input=token.encode(),
            capture_output=True,
        )
    except FileNotFoundError:
        print(RED("gpg not found. Install GnuPG and ensure a key pair exists."), file=sys.stderr)
        return 1

    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        print(RED(f"GPG encryption failed:\n  {stderr}"), file=sys.stderr)
        return 1

    # Save the token file path into config.
    try:
        mgr.set_server_token(workspace_name, server_name, str(token_file))
        mgr.save()
    except ValueError as e:
        print(RED(str(e)), file=sys.stderr)
        return 1

    print(GREEN(f"Token encrypted and saved to: {token_file}"))
    print(DIM(f"Config updated: workspace '{workspace_name}', server '{server_name}'"))
    return 0
