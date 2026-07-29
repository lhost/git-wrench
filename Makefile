
.DEFAULT_GOAL := help

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

#		$$(uv tree --depth 1 --no-dev --preview-features json-output --format json \
#		    | jq -r '.resolution | map(select(.kind == "package") | .name)[]')
DEPENDENCIES =$(shell $(UV) tomlq -r ' \
			  .project.dependencies[] | \
			  sub(";.*$$"; "") | \
			  sub("\\[.*\\]"; "") | \
			  sub("(==|>=|<=|~=|!=|>|<).*"; "") \
			  ' pyproject.toml \
)

DEPENDENCIES_DEV =$(shell $(UV) tomlq -r ' \
				  .["dependency-groups"].dev[] | \
				  sub(";.*$$"; "") | \
				  sub("\\[.*\\]"; "") | \
				  sub("(==|>=|<=|~=|!=|>|<).*"; "") \
				  ' pyproject.toml \
)

.PHONY: uv.lock requirements.txt

install: ## install required dependencies
	uv sync --group dev
	$(UV) pre-commit install

sync:
	uv sync

up update:: uv.lock requirements.txt
	$(UV) pre-commit autoupdate

uv.lock:
	uv sync --group dev

requirements.txt:
	uv export --format requirements.txt --output-file $@

upgrade:
	@echo DEPENDENCIES=$(DEPENDENCIES)
	uv add --upgrade $(DEPENDENCIES)

upgrade-dev:
	@echo DEPENDENCIES_DEV=$(DEPENDENCIES_DEV)
	uv add --group dev --upgrade $(DEPENDENCIES_DEV)


dep: uv.lock requirements.txt

hooks:
	$(UV) pre-commit run --all-files

.git/hooks/pre-commit:
	$(UV) pre-commit install

.PHONY: help
help: ## print this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

format: ## fix formatting
	$(UV) ruff format .

test-format:
	$(UV) ruff format --check .

test-lint:
	$(UV) ruff check .

fix: ## fix python code
	$(UV) ruff check . --fix

test-typecheck:
	$(UV) pyright

test-pytest:
	$(UV) pytest

test-coverage:
	$(UV) pytest --cov

test-secrets:
	@echo "--- Running detect-secrets `$(UV) detect-secrets --version` ---"
	@git ls-files -z -- \
		| xargs -0 $(UV) detect-secrets-hook --baseline .secrets.baseline

scan: ## run detect-secrets
	$(UV) detect-secrets scan --update .secrets.baseline

audit:
	$(UV) detect-secrets audit .secrets.baseline

test-security:
	$(UV) bandit -r . -c pyproject.toml

test-audit:
	$(UV) pip-audit

test:: test-format test-lint test-typecheck test-pytest test-secrets test-security test-audit ## run tests

clean: ## cleanup Untitled documents and empty directories
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	rm -rf htmlcov
	rm -f .coverage

# vim: fdm=marker
