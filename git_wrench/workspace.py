"""
Workspace model and manager for git-wrench.

A Workspace is a named root directory that is searched for git repositories.

    from git_wrench.workspace import WorkspaceManager

    mgr = WorkspaceManager.load()
    mgr.add("personal", "~/projects")
    mgr.rename("personal", "home")
    mgr.remove("home")
    mgr.save()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from . import config as cfg

# ── models ────────────────────────────────────────────────────────────────────

ServerType = Literal["github", "gitlab", "gitolite"]
VALID_SERVER_TYPES: tuple[str, ...] = ("github", "gitlab", "gitolite")


@dataclass
class GitServer:
    """A remote git server associated with a workspace."""

    type: str  # "github" | "gitlab" | "gitolite"
    name: str  # short identifier, e.g. "origin"
    url: str  # e.g. "git.example.com" or "https://github.com"

    def to_dict(self) -> dict[str, str]:
        return {
            "server_type": self.type,
            "server_name": self.name,
            "server_url": self.url,
        }

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> GitServer:
        return cls(
            type=d.get("server_type", ""),
            name=d.get("server_name", ""),
            url=d.get("server_url", ""),
        )

    def __str__(self) -> str:
        return f"{self.name}  ({self.type})  {self.url}"


@dataclass
class Workspace:
    name: str
    path: str  # stored as-is (may contain ~); expand with .resolved_path
    servers: list[GitServer] = field(default_factory=list)

    @property
    def resolved_path(self) -> Path:
        """Return the path expanded and resolved to an absolute Path."""
        return Path(self.path).expanduser().resolve()

    def to_dict(self) -> dict:
        d: dict = {"name": self.name, "path": self.path}
        if self.servers:
            d["servers"] = [s.to_dict() for s in self.servers]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Workspace:
        servers = [GitServer.from_dict(s) for s in d.get("servers", [])]
        return cls(name=d.get("name", ""), path=d.get("path", ""), servers=servers)

    def __str__(self) -> str:
        return f"{self.name}  ({self.path})"


# ── manager ───────────────────────────────────────────────────────────────────


class WorkspaceManager:
    """In-memory list of Workspace objects backed by the git-wrench config file."""

    def __init__(self, conf: dict, workspaces: list[Workspace]) -> None:
        self._conf = conf
        self._workspaces = workspaces

    # ── factory ───────────────────────────────────────────────────────────────

    @classmethod
    def load(cls) -> WorkspaceManager:
        """Load workspaces from the config file on disk."""
        conf = cfg.load()
        entries = cfg.workspace_list(conf)
        return cls(conf, [Workspace.from_dict(e) for e in entries])

    # ── query ─────────────────────────────────────────────────────────────────

    def all(self) -> list[Workspace]:
        """Return all workspaces (ordered)."""
        return list(self._workspaces)

    def get(self, name: str) -> Workspace | None:
        """Return the workspace with *name*, or None."""
        for ws in self._workspaces:
            if ws.name == name:
                return ws
        return None

    def paths(self) -> list[Path]:
        """Return resolved paths for all workspaces."""
        return [ws.resolved_path for ws in self._workspaces]

    # ── mutations ─────────────────────────────────────────────────────────────

    def add(self, name: str, path: str) -> Workspace:
        """Add a new workspace.  Raises ValueError if name already exists."""
        if self.get(name) is not None:
            raise ValueError(f"Workspace '{name}' already exists.")
        ws = Workspace(name=name, path=path)
        self._workspaces.append(ws)
        return ws

    # ── server mutations ──────────────────────────────────────────────────────

    def add_server(
        self,
        workspace_name: str,
        server_type: str,
        server_name: str,
        server_url: str,
    ) -> GitServer:
        """Add a git server to a workspace.  Raises ValueError on bad input."""
        if server_type not in VALID_SERVER_TYPES:
            raise ValueError(f"Unknown server type '{server_type}'. Valid types: {', '.join(VALID_SERVER_TYPES)}")
        ws = self.get(workspace_name)
        if ws is None:
            raise ValueError(f"Workspace '{workspace_name}' not found.")
        for s in ws.servers:
            if s.name == server_name:
                raise ValueError(f"Server '{server_name}' already exists in workspace '{workspace_name}'.")
        server = GitServer(type=server_type, name=server_name, url=server_url)
        ws.servers.append(server)
        return server

    def remove_server(self, workspace_name: str, server_name: str) -> GitServer:
        """Remove a git server from a workspace.  Raises ValueError if not found."""
        ws = self.get(workspace_name)
        if ws is None:
            raise ValueError(f"Workspace '{workspace_name}' not found.")
        for s in ws.servers:
            if s.name == server_name:
                ws.servers.remove(s)
                return s
        raise ValueError(f"Server '{server_name}' not found in workspace '{workspace_name}'.")

    def list_servers(self, workspace_name: str) -> list[GitServer]:
        """Return the servers configured for *workspace_name*."""
        ws = self.get(workspace_name)
        if ws is None:
            raise ValueError(f"Workspace '{workspace_name}' not found.")
        return list(ws.servers)

    def rename(self, old_name: str, new_name: str) -> Workspace:
        """Rename a workspace.  Raises ValueError if not found or name taken."""
        ws = self.get(old_name)
        if ws is None:
            raise ValueError(f"Workspace '{old_name}' not found.")
        if old_name != new_name and self.get(new_name) is not None:
            raise ValueError(f"Workspace '{new_name}' already exists.")
        ws.name = new_name
        return ws

    def update_path(self, name: str, new_path: str) -> Workspace:
        """Change the path of an existing workspace."""
        ws = self.get(name)
        if ws is None:
            raise ValueError(f"Workspace '{name}' not found.")
        ws.path = new_path
        return ws

    def remove(self, name: str) -> Workspace:
        """Remove a workspace by name.  Raises ValueError if not found."""
        ws = self.get(name)
        if ws is None:
            raise ValueError(f"Workspace '{name}' not found.")
        self._workspaces.remove(ws)
        return ws

    # ── persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist current workspace list to config.toml."""
        self._conf.setdefault("workspaces", {})["list"] = [ws.to_dict() for ws in self._workspaces]
        cfg.save(self._conf)

    def reload(self) -> None:
        """Re-read config from disk and refresh the workspace list."""
        self._conf = cfg.load()
        entries = cfg.workspace_list(self._conf)
        self._workspaces = [Workspace.from_dict(e) for e in entries]
