from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    pass


def main(argv: list[str] | None = None) -> int:
    from main import main as _main

    return _main(argv)


__all__ = ["main"]
