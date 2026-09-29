# Default target
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

MKDOCS = mkdocs
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
.PHONY: wakemeops-keyring.asc

install: ## install git-wrench via Homebrew from local formula
	$(eval VERSION := $(shell uv run tomlq -r '.project.version' pyproject.toml))
	$(eval TARBALL := /tmp/git-wrench-$(VERSION).tar.gz)
	rm -f $(TARBALL)
	brew cleanup --prune=all git-wrench 2>/dev/null || true
	git archive --format=tar.gz --prefix=git-wrench-$(VERSION)/ HEAD > $(TARBALL)
	brew tap lhost/git-wrench $(PWD) || true
	brew trust lhost/git-wrench
	sed "s|url \"https://github.com/lhost/git-wrench/archive/refs/tags/v[^\"]*\"|url \"file://$(TARBALL)\"\n  version \"$(VERSION)\"|; /sha256/d" \
	    $(PWD)/Formula/git-wrench.rb \
	    > $$(brew --repository lhost/git-wrench)/Formula/git-wrench.rb
	brew uninstall --force git-wrench 2>/dev/null || true
	brew install --build-from-source git-wrench

install-dev: ## install required dependencies for local development (developers only)
	uv sync --group dev
	$(UV) pre-commit install

sync:
	uv sync

up update: uv.lock requirements.txt wakemeops-keyring.asc
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

wakemeops-keyring.asc:
	curl -sSL https://raw.githubusercontent.com/upciti/wakemeops/main/assets/install_repository | \
		sed -n '/-----BEGIN PGP PUBLIC KEY BLOCK-----/,/-----END PGP PUBLIC KEY BLOCK-----/p' > $@

dep: uv.lock requirements.txt

test-dep: ## Check that requirements.txt is in sync with uv.lock
	@uv export --format requirements.txt --output-file /tmp/.requirements.txt.check > /dev/null
	@grep -v '^#' requirements.txt > /tmp/.requirements.txt.committed
	@grep -v '^#' /tmp/.requirements.txt.check > /tmp/.requirements.txt.fresh
	@if ! diff -q /tmp/.requirements.txt.committed /tmp/.requirements.txt.fresh > /dev/null 2>&1; then \
	   echo ""; \
	   echo "ERROR: requirements.txt is out of sync with uv.lock."; \
	   echo ""; \
	   echo "Diff (committed vs. current export):"; \
	   diff -u /tmp/.requirements.txt.committed /tmp/.requirements.txt.fresh || true; \
	   echo ""; \
	   echo "Fix: run 'make dep' locally and commit the updated requirements.txt."; \
	   exit 1; \
	 fi
	@echo "OK: requirements.txt is in sync with uv.lock."

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

scan: ## run detect-secrets
	$(UV) detect-secrets scan --update .secrets.baseline

audit:
	$(UV) detect-secrets audit .secrets.baseline

test-secrets: ## detect-secrets: verify baseline is up-to-date and all findings are audited
	@echo "--- detect-secrets $(shell $(UV) detect-secrets --version) ---"
	@cp .secrets.baseline /tmp/.secrets.baseline.check
	@$(UV) detect-secrets scan --update /tmp/.secrets.baseline.check
	@jq '{results,plugins_used,version,word_list}' .secrets.baseline            > /tmp/.secrets.baseline.committed
	@jq '{results,plugins_used,version,word_list}' /tmp/.secrets.baseline.check > /tmp/.secrets.baseline.fresh
	@if ! diff -q /tmp/.secrets.baseline.committed /tmp/.secrets.baseline.fresh > /dev/null 2>&1; then \
	   echo ""; \
	   echo "ERROR: .secrets.baseline is out of date."; \
	   echo "New findings or removed files were detected since the last 'make scan'."; \
	   echo ""; \
	   echo "Diff (committed vs. current scan):"; \
	   diff -u /tmp/.secrets.baseline.committed /tmp/.secrets.baseline.fresh || true; \
	   echo ""; \
	   echo "Fix: run 'make scan' locally, audit any new findings with 'make audit',"; \
	   echo "     then commit the updated .secrets.baseline."; \
	   exit 1; \
	 fi
	@unaudited=$$(jq -r '.results | to_entries[] | .key as $$f | .value[] | select(.is_secret == null) | "\($$f):\(.line_number) [\(.type)]"' /tmp/.secrets.baseline.check); \
	 if [ -n "$$unaudited" ]; then \
	   echo ""; \
	   echo "ERROR: unaudited findings in .secrets.baseline (is_secret is null)."; \
	   echo "Run 'make audit' to review each entry and mark it is_secret: true/false."; \
	   echo ""; \
	   echo "Unaudited entries:"; \
	   echo "$$unaudited"; \
	   echo ""; \
	   exit 1; \
	 fi
	@echo "OK: .secrets.baseline is up-to-date and all findings are audited."

test-security:
	$(UV) bandit -r . -c pyproject.toml

test-audit:
	$(UV) pip-audit

test:: test-format test-lint test-typecheck test-pytest test-secrets test-security test-audit test-build ## run tests

test-build:
	$(UV) $(MKDOCS) build --strict

build:
	$(UV) $(MKDOCS) build --config-file mkdocs.yml --strict

serve: ## start local server for website development
	$(UV) $(MKDOCS) serve --livereload -o --dev-addr 127.0.0.1:13800

deploy: ## generate new version of static website from markdown files
	$(UV) $(MKDOCS) gh-deploy --config-file mkdocs.yml --remote-branch gh-pages
	git push gitolite gh-pages origin/gh-pages

deb: ## build Debian package using dpkg-buildpackage
	@mkdir -p dist/deb
	dpkg-buildpackage -us -uc -b
	find .. -maxdepth 1 -type f \
		\( -name '*.deb' -o -name '*.changes' -o -name '*.buildinfo' \) \
		-exec mv {} dist/deb/ \;

rpm: ## build RPM package using rpmbuild
	@VERSION=$$(sed -n 's/^version *= *"\([^"]*\)".*/\1/p' pyproject.toml); \
	TOPDIR="$$(pwd)/dist/rpmbuild"; \
	mkdir -p "$${TOPDIR}/BUILD" "$${TOPDIR}/BUILDROOT" "$${TOPDIR}/RPMS" "$${TOPDIR}/SOURCES" "$${TOPDIR}/SPECS" "$${TOPDIR}/SRPMS"; \
	cp git-wrench.spec "$${TOPDIR}/SPECS/git-wrench.spec"; \
	git archive --format=tar.gz --prefix=git-wrench-$${VERSION}/ HEAD > "$${TOPDIR}/SOURCES/git-wrench-$${VERSION}.tar.gz"; \
	rpmbuild --define "_topdir $${TOPDIR}" -ba "$${TOPDIR}/SPECS/git-wrench.spec"

clean-homebrew: ## remove Homebrew tap
	#brew uninstall --force git-wrench 2>/dev/null || true
	brew untap lhost/git-wrench 2>/dev/null || true

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

GEN_BADGE_VAL = posts-count.svg

generate-badge:
	@COUNT=$$(find docs/ -name "*.md" | wc -l); \
	printf '<svg xmlns="http://www.w3.org/2000/svg" width="90" height="20">\
	<rect width="60" height="20" fill="#555"/><rect x="60" width="30" height="20" fill="#4c1"/>\
	<g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">\
	<text x="30" y="14">posts</text><text x="75" y="14">%s</text></g></svg>' "$$COUNT" > $(GEN_BADGE_VAL)
	@echo "Posts Count badge generated: $$COUNT posts"

# vim: fdm=marker
