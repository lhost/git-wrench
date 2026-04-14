import sys

import typer

from git_wrench.commands import status, sync, workspace


app = typer.Typer()

app.command()(sync)
app.command()(status)
app.command()(workspace)


def main():
    return app(sys.argv[1:])
