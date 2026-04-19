"""
git_server – adapters for listing repositories from remote git servers.

Each adapter implements :class:`GitServerAdapter` and is registered by
server type.  Use :func:`get_adapter` to obtain the right one.

    from git_wrench.git_server import get_adapter

    adapter = get_adapter("gitolite", url="git.example.com")
    repos = adapter.list_repos()
"""

from __future__ import annotations

from .base import GitServerAdapter
from .github import GitHubAdapter
from .gitlab import GitLabAdapter
from .gitolite import GitoliteAdapter

_ADAPTERS: dict[str, type[GitServerAdapter]] = {
    "github": GitHubAdapter,
    "gitlab": GitLabAdapter,
    "gitolite": GitoliteAdapter,
}


def get_adapter(server_type: str, url: str) -> GitServerAdapter:
    """Return a :class:`GitServerAdapter` instance for *server_type*.

    Raises :class:`ValueError` for unknown server types.
    """
    cls = _ADAPTERS.get(server_type)
    if cls is None:
        raise ValueError(f"Unknown server type '{server_type}'. Valid types: {', '.join(sorted(_ADAPTERS))}")
    return cls(url)


__all__ = [
    "GitServerAdapter",
    "GitHubAdapter",
    "GitLabAdapter",
    "GitoliteAdapter",
    "get_adapter",
]
