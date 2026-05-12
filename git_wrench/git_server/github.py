"""
GitHub adapter – list repositories via the GitHub REST API v3.

Authentication (optional but recommended to avoid rate limiting):
  Set the environment variable  GITHUB_TOKEN  to a personal access token.

The *url* passed to the adapter is used as the API base, so it supports
GitHub Enterprise as well as github.com:

    GitHubAdapter("https://github.com")             # public GitHub
    GitHubAdapter("https://github.example.com")     # GitHub Enterprise
"""

from __future__ import annotations

import json
import os
import urllib.request
from urllib.error import URLError

from .base import GitServerAdapter, RemoteRepo

_DEFAULT_URL = "https://github.com"
_API_URL = "https://api.github.com"
_ALLOWED_SCHEMES = ("https://", "git://", "git+ssh://")


class GitHubAdapter(GitServerAdapter):
    """Lists repositories for an authenticated user via the GitHub API."""

    def __init__(self, url: str = _DEFAULT_URL, *, token: str = "") -> None:
        super().__init__(url)
        if not self.url.startswith(_ALLOWED_SCHEMES):
            raise ValueError(f"GitHubAdapter requires an http/https/git/git+ssh URL, got: {self.url!r}")
        self._token = token

    def list_repos(self) -> list[RemoteRepo]:
        """Return all repositories accessible with the configured token.

        Paginates automatically.  Pass a plaintext token via the constructor or
        set GITHUB_TOKEN in the environment; without either only public repos
        are returned (subject to rate limiting).
        """
        token = self._token or os.environ.get("GITHUB_TOKEN", "")
        # Determine API base: github.com → api.github.com; GHE keeps same host
        if self.url.rstrip("/") in (_DEFAULT_URL, _DEFAULT_URL.rstrip("/")):
            api_base = _API_URL
        else:
            api_base = self.url.rstrip("/") + "/api/v3"

        repos: list[RemoteRepo] = []
        page = 1
        while True:
            endpoint = f"{api_base}/user/repos?per_page=100&page={page}"
            req = urllib.request.Request(endpoint)
            req.add_header("Accept", "application/vnd.github+json")
            req.add_header("X-GitHub-Api-Version", "2022-11-28")
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
                    data: list[dict] = json.load(resp)
            except URLError as exc:
                raise RuntimeError(f"GitHub API request failed: {exc}") from exc

            if not data:
                break
            for item in data:
                repos.append(
                    RemoteRepo(
                        name=item["name"],
                        clone_url=item.get("clone_url", item.get("ssh_url", "")),
                        description=item.get("description") or "",
                    )
                )
            if len(data) < 100:
                break
            page += 1

        return repos
