"""Shared ANSI colour helpers for CLI output."""

from __future__ import annotations

import sys

_NO_COLOR = not sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if _NO_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def BLACK(t: str) -> str:
    return _c("30", t)


def RED(t: str) -> str:
    return _c("31", t)


def GREEN(t: str) -> str:
    return _c("32", t)


def YELLOW(t: str) -> str:
    return _c("33", t)


def BLUE(t: str) -> str:
    return _c("34", t)


def MAGENTA(t: str) -> str:
    return _c("35", t)


def CYAN(t: str) -> str:
    return _c("36", t)


def WHITE(t: str) -> str:
    return _c("37", t)


def BOLD(t: str) -> str:
    return _c("1", t)


def DIM(t: str) -> str:
    return _c("2", t)


def __main__() -> None:
    print(RED("RED: Hello, world!"))
    print(GREEN("GREEN: Hello, world!"))
    print(YELLOW("YELLOW: Hello, world!"))
    print(BLUE("BLUE: Hello, world!"))
    print(MAGENTA("MAGENTA: Hello, world!"))
    print(CYAN("CYAN: Hello, world!"))
    print(WHITE("WHITE: Hello, world!"))
    print(BOLD("BOLD: Hello, world!"))
    print(DIM("DIM: Hello, world!"))


if __name__ == "__main__":
    __main__()
