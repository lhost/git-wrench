"""
git-wrench – entry point (development helper).

The real implementation lives in git_wrench/cli.py so it is included in the
installed package.  This file delegates to it and is only used when running
directly from the source tree (e.g. `python main.py`).
"""

from __future__ import annotations

import sys

from git_wrench.cli import main  # noqa: F401 – re-exported for `python main.py`

if __name__ == "__main__":
    sys.exit(main())
