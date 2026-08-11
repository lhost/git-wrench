"""
git_server – adapters for listing repositories from remote git servers.

Each adapter implements :class:`GitServerAdapter` and is registered by
server type.  Use :func:`get_adapter` to obtain the right one.

    from git_wrench.git_server import get_adapter

    adapter = get_adapter("gitolite", url="git.example.com")
    repos = adapter.list_repos()
"""

from __future__ import annotations

import subprocess  # nosec B404
from pathlib import Path

from .base import GitServerAdapter
from .github import GitHubAdapter
from .gitlab import GitLabAdapter
from .gitolite import GitoliteAdapter

_ADAPTERS: dict[str, type[GitServerAdapter]] = {
    "github": GitHubAdapter,
    "gitlab": GitLabAdapter,
    "gitolite": GitoliteAdapter,
}


def resolve_token(token_path: str) -> str:
    """Decrypt a GPG-encrypted token file and return the plaintext token.

    *token_path* is the path to an ASCII-armoured (.asc) file encrypted with
    GPG.  The file is decrypted with::

        gpg --quiet --batch --decrypt < <token_path>

    Returns an empty string if *token_path* is empty.
    Raises :class:`RuntimeError` if decryption fails.
    """
    if not token_path:
        return ""
    path = Path(token_path).expanduser()
    try:
        result = subprocess.run(  # nosec B603 B607
            ["gpg", "--quiet", "--batch", "--decrypt"],
            stdin=path.open("rb"),
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"gpg not found: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace").strip()
        raise RuntimeError(f"GPG decryption failed for {token_path!r}: {stderr}") from exc
    return result.stdout.decode().strip()


def get_adapter(server_type: str, url: str, token: str = "") -> GitServerAdapter:
    """Return a :class:`GitServerAdapter` instance for *server_type*.

    *token* is the already-resolved plaintext API token.  When omitted the
    adapter falls back to its environment-variable default.

    Raises :class:`ValueError` for unknown server types.
    """
    cls = _ADAPTERS.get(server_type)
    if cls is None:
        raise ValueError(f"Unknown server type '{server_type}'. Valid types: {', '.join(sorted(_ADAPTERS))}")
    return cls(url, token=token)


__all__ = [
    "GitServerAdapter",
    "GitHubAdapter",
    "GitLabAdapter",
    "GitoliteAdapter",
    "get_adapter",
    "resolve_token",
]
