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

from dataclasses import dataclass
from pathlib import Path

from . import config as cfg

# ── model ─────────────────────────────────────────────────────────────────────


@dataclass
class Workspace:
    name: str
    path: str  # stored as-is (may contain ~); expand with .resolved_path

    @property
    def resolved_path(self) -> Path:
        """Return the path expanded and resolved to an absolute Path."""
        return Path(self.path).expanduser().resolve()

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "path": self.path}

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> Workspace:
        return cls(name=d.get("name", ""), path=d.get("path", ""))

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
