
# termninal colors # {{{
BLACK=30
RED=31
GREEN=32
YELLOW=33
BLUE=34
MAGENTA=35
CYAN=36
WHITE=37

RESET=\\033[0m
BOLD=1
UNDERLINE=4
BLINK=5
REVERSE=7

BOLD_GREEN=\\033[${BOLD};${GREEN}m
BOLD_RED=\\033[${BOLD};${RED}m
BOLD_YELLOW=\\033[${BOLD};${YELLOW}m
BOLD_MAGENTA=\\033[${BOLD};${MAGENTA}m
BOLD_BLUE=\\033[${BOLD};${BLUE}m
BOLD_CYAN=\\033[${BOLD};${CYAN}m
# }}}

UV = uv run

install:
	uv sync --group dev
	$(UV) pre-commit install

update::
	$(UV) pre-commit autoupdate

.git/hooks/pre-commit:
	$(UV) pre-commit install

test::

clean:
	rm -rf __pycache__

# vim: fdm=marker
