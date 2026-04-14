
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

.PHONY: uv.lock requirements.txt

UV = uv run

install:
	uv sync --group dev
	$(UV) pre-commit install

sync:
	uv sync

update:: uv.lock
	$(UV) pre-commit autoupdate

uv.lock:
	uv sync --group dev

dep: uv.lock requirements.txt

requirements.txt:
	uv export --format requirements.txt --output-file $@

hooks:
	$(UV) pre-commit run --all-files

.git/hooks/pre-commit:
	$(UV) pre-commit install

format:
	$(UV) ruff format .

test-format:
	$(UV) ruff format --check .


test-lint:
	$(UV) ruff check .

fix:
	$(UV) ruff check . --fix

test:: test-pytest
test-pytest:
	$(UV) pytest


clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +

# vim: fdm=marker
