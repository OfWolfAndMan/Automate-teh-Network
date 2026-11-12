# Thin harness around the pinned toolchain. README explains what the repo is; this file
# only makes the commands identical on every machine, including CI.

PY ?= python3

.PHONY: help setup inventory preflight lint syntax docs-check scrub pytest compliance show test full e2e-linux e2e-network lab-up lab-down index index-check

help:
	@printf '%-12s %s\n' \
	  setup     "install the pinned ansible-core and collections" \
	  inventory "parse and graph the lab inventory" \
	  preflight "run the preflight gates (needs a vault password)" \
	  syntax    "ansible-playbook --syntax-check over playbooks/" \
	  lint      "yamllint + ansible-lint + syntax-check" \
	  scrub     "SHIELD gate: fail if a credential, address or identifier would publish" \
	  docs-check "markdown structure of README and docs/" \
	  pytest    "unit tests: the compliance filter and the examples" \
	  compliance "the compliance playbook, end to end, against the fixtures" \
	  show      "show.yml parse + save, end to end, against saved captures" \
	  test      "the whole harness, in order"

setup:
	$(PY) -m pip install --quiet -r requirements.txt -r examples/python/requirements.txt
	ansible-galaxy collection install -r requirements.yml -p ./collections

inventory:
	ansible-inventory -i inventories/lab/hosts.yml --graph

preflight:
	ansible-playbook playbooks/preflight.yml --ask-vault-pass

syntax:
	@set -e; for f in playbooks/*.yml playbooks/*/*.yml; do echo "  $$f"; \
	  ansible-playbook --syntax-check -i inventories/lab/hosts.yml "$$f" >/dev/null; done; \
	  echo "  syntax ok"

lint: syntax
	yamllint -f parsable -c .yamllint.yml .
	ruff check .
	ansible-lint playbooks/ || true

e2e-linux:
	bash scripts/e2e_linux.sh

e2e-network:
	bash scripts/e2e_network.sh

lab-up:
	containerlab deploy -t lab/network.clab.yml

lab-down:
	containerlab destroy -t lab/network.clab.yml --cleanup

index:
	$(PY) tools/gen_index.py --write

index-check:
	$(PY) tools/gen_index.py --check

docs-check:
	@if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
	  docker run --rm -v "$(PWD):/w" -w /w node:20-alpine \
	    npx --yes markdownlint-cli2 'docs/*.md' 'README.md' 'tests/fixtures/*.md' 'examples/**/*.md'; \
	elif command -v npx >/dev/null 2>&1; then \
	  npx --yes markdownlint-cli2 'docs/*.md' 'README.md' 'tests/fixtures/*.md' 'examples/**/*.md'; \
	else \
	  echo "SKIP: neither docker nor npx available"; \
	fi

scrub:
	$(PY) tools/shield/sanitize.py --check .

pytest:
	$(PY) -m pytest

compliance:
	bash scripts/e2e_compliance.sh

show:
	bash scripts/e2e_show.sh

test: scrub inventory syntax index-check docs-check pytest compliance show
	@echo "harness ok"

full: test e2e-linux
	@echo "harness + lab layer 1 ok"
