"""
Base class for git server adapters.

All adapters must subclass :class:`GitServerAdapter` and implement
:meth:`list_repos`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RemoteRepo:
    """Minimal description of a repository available on a remote server."""

    name: str  # short repo name, e.g. "myproject"
    clone_url: str  # full URL suitable for `git clone`
    description: str = ""


class GitServerAdapter(ABC):
    """Abstract base for all git server adapters."""

    def __init__(self, url: str, *, token: str = "") -> None:
        self.url = url.rstrip("/")
        self._token = token

    @abstractmethod
    def list_repos(self) -> list[RemoteRepo]:
        """Return the list of repositories available on this server."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(url={self.url!r})"
