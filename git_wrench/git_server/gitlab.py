"""
GitLab adapter – list repositories via the GitLab REST API v4.

Authentication (optional but recommended):
  Set the environment variable  GITLAB_TOKEN  to a personal access token.

The *url* is the GitLab instance base URL, e.g.:
    GitLabAdapter("https://gitlab.com")
    GitLabAdapter("https://gitlab.example.com")
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError

from .base import GitServerAdapter, RemoteRepo

_ALLOWED_SCHEMES = ("https://", "git://", "git+ssh://")


def _inject_token(http_url: str, token: str) -> str:
    """Return *http_url* with ``oauth2:<token>@`` inserted before the host.

    Example::
        https://gitlab.example.com/group/repo.git
        → https://oauth2:<token>@gitlab.example.com/group/repo.git
    """
    parsed = urllib.parse.urlparse(http_url)
    authed = parsed._replace(netloc=f"oauth2:{token}@{parsed.hostname}" + (f":{parsed.port}" if parsed.port else ""))
    return urllib.parse.urlunparse(authed)


class GitLabAdapter(GitServerAdapter):
    """Lists repositories accessible via the GitLab API."""

    def __init__(self, url: str, *, token: str = "") -> None:
        super().__init__(url)
        if not self.url.startswith(_ALLOWED_SCHEMES):
            raise ValueError(f"GitLabAdapter requires an http/https/git/git+ssh URL, got: {self.url!r}")
        self._token = token

    def list_repos(self) -> list[RemoteRepo]:
        """Return all projects (repositories) accessible with the configured token.

        Paginates automatically.  Pass a plaintext token via the constructor or
        set GITLAB_TOKEN in the environment to include private/internal projects.
        Without a token, only public projects visible to anonymous users are returned.
        """
        token = self._token or os.environ.get("GITLAB_TOKEN", "")
        api_base = self.url.rstrip("/") + "/api/v4"

        repos: list[RemoteRepo] = []
        page = 1
        while True:
            query: dict = {
                "per_page": 100,
                "page": page,
                "order_by": "name",
                "sort": "asc",
            }
            # membership=true limits results to projects the authenticated user
            # belongs to.  Without a token the filter silently returns nothing,
            # so only apply it when we actually have credentials.
            if token:
                query["membership"] = "true"
            params = urllib.parse.urlencode(query)
            endpoint = f"{api_base}/projects?{params}"
            req = urllib.request.Request(endpoint)
            if token:
                req.add_header("PRIVATE-TOKEN", token)
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
                    data: list[dict] = json.load(resp)
            except HTTPError as exc:
                raise RuntimeError(f"GitLab API request failed: HTTP {exc.code} {exc.reason}") from exc
            except URLError as exc:
                raise RuntimeError(f"GitLab API request failed: {exc}") from exc

            if not data:
                break
            for item in data:
                http_url = item.get("http_url_to_repo", "")
                ssh_url = item.get("ssh_url_to_repo", "")
                # Prefer HTTPS when a token is available so we can embed
                # credentials directly in the URL:
                #   https://oauth2:<token>@host/group/repo.git
                # Fall back to SSH URL when there is no token.
                if token and http_url:
                    clone_url = _inject_token(http_url, token)
                else:
                    clone_url = http_url or ssh_url
                repos.append(
                    RemoteRepo(
                        name=item.get("path", item.get("name", "")),
                        clone_url=clone_url,
                        description=item.get("description") or "",
                    )
                )
            if len(data) < 100:
                break
            page += 1

        return repos
