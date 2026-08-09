"""
git-wrench – entry point.

Hot path (performance)
──────────────────────
The command modules (sync, status, …) are never imported here.
main() only imports `git_wrench.registry`, which itself has no heavy deps.
Each command module is imported by the registry on first dispatch only.

Usage
─────
  git-wrench              # open interactive TUI
  git-wrench sync         # pull all repos in configured workspaces
  git-wrench sync --path <dir>
  git-wrench status       # show repo overview table
  git-wrench --help
  git-wrench --help <command>
"""

from __future__ import annotations

import sys


def _help() -> str:
    # Import registry only to list known commands + their one-liners.
    # Command modules are NOT imported here — discovery triggers @command
    # decorators which only store strings.
    from git_wrench import commands as _cmd_pkg  # triggers @command decorators
    from git_wrench import registry

    _cmd_pkg._discover()

    lines = [
        "git-wrench  – multi-repo git workspace manager",
        "",
        "Usage:",
        "  git-wrench                        Open interactive TUI",
    ]
    for name in registry.names():
        hint = registry.help_text(name)
        lines.append(f"  git-wrench {name:<22} {hint}")
    lines += [
        "",
        "Options:",
        "  -h, --help             Show this help and exit",
        "  -h, --help <command>   Show detailed help for a command",
        "",
        "Config file: ~/.config/git-wrench/config.toml",
        "  (created automatically with defaults on first run)",
    ]
    return "\n".join(lines)


def _command_help(cmd: str) -> str:
    """Return the long help text for *cmd*, falling back to the one-liner."""
    import importlib

    import git_wrench.registry as registry

    # Import the module so its @command decorator fires and populates the registry.
    try:
        importlib.import_module(f"git_wrench.commands.{cmd}")
    except ModuleNotFoundError:
        return f"git-wrench: unknown command '{cmd}'. Run 'git-wrench --help'."

    long = registry.long_help_text(cmd)
    if long:
        return long.strip()
    one = registry.help_text(cmd)
    return f"{cmd}: {one}" if one else f"No help available for '{cmd}'."


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        # no args → launch TUI (heavy curses import deferred until here)
        from git_wrench import config as cfg
        from git_wrench.tui import run_tui

        conf = cfg.load()
        try:
            run_tui(conf)
        except KeyboardInterrupt:
            pass
        return 0

    # --help <command>  or  <command> --help
    if argv[0] in ("-h", "--help") and len(argv) >= 2:
        print(_command_help(argv[1]))
        return 0

    if argv[0] in ("-h", "--help"):
        print(_help())
        return 0

    cmd, rest = argv[0], argv[1:]

    if "--help" in rest or "-h" in rest:
        print(_command_help(cmd))
        return 0

    # Trigger @command decorators for this one module only, then dispatch.
    # The import of git_wrench.commands.sync (for example) is done inside
    # registry.dispatch() via importlib — no other command module is touched.
    from git_wrench import registry

    # Seed the registry: import just the target command module so its
    # @command decorator fires before we call dispatch().
    _module = f"git_wrench.commands.{cmd}"
    try:
        import importlib

        importlib.import_module(_module)
    except ModuleNotFoundError:
        print(f"git-wrench: unknown command '{cmd}'. Run 'git-wrench --help'.", file=sys.stderr)
        return 1

    rc = registry.dispatch(cmd, rest)
    if rc is None:
        print(f"git-wrench: unknown command '{cmd}'. Run 'git-wrench --help'.", file=sys.stderr)
        return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
