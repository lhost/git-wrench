"""
Gitolite adapter – list repositories via the `ssh` Gitolite info command.

The *url* should be the SSH host (and optional user), e.g.:
    GitoliteAdapter("git@git.example.com")
    GitoliteAdapter("gitolite@git.company.internal")

Gitolite responds to ``ssh <host> info`` with a list of accessible repos.
"""

from __future__ import annotations

import subprocess

from .base import GitServerAdapter, RemoteRepo


class GitoliteAdapter(GitServerAdapter):
    """Lists repositories by running ``ssh <host> info`` against a Gitolite server."""

    def list_repos(self) -> list[RemoteRepo]:
        """Return all repositories reported by ``ssh <host> info``.

        Requires that the SSH key for the current user is already authorised on
        the Gitolite server.

        Raises :class:`RuntimeError` if the SSH command fails.
        """
        try:
            result = subprocess.run(
                ["ssh", self.url, "info"],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except FileNotFoundError:
            raise RuntimeError("'ssh' executable not found.") from None
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"SSH connection to '{self.url}' timed out.") from None

        if result.returncode != 0:
            raise RuntimeError(f"Gitolite info command failed (exit {result.returncode}):\n{result.stderr.strip()}")

        return self._parse_info(result.stdout)

    # ── parsing ───────────────────────────────────────────────────────────────

    def _parse_info(self, output: str) -> list[RemoteRepo]:
        """Parse the output of ``ssh <host> info``.

        Gitolite output looks like::

            hello user, this is git@host running gitolite3 …

             R W    repo-name
             R      another-repo
            @all    testing
        """
        repos: list[RemoteRepo] = []
        for line in output.splitlines():
            # skip header / blank lines
            stripped = line.strip()
            if not stripped or stripped.startswith("hello ") or stripped.startswith("@"):
                continue
            # permissions column(s) followed by repo name
            parts = stripped.split()
            if len(parts) >= 2:
                repo_name = parts[-1]
                repos.append(
                    RemoteRepo(
                        name=repo_name,
                        clone_url=f"{self.url}:{repo_name}",
                    )
                )
        return repos
