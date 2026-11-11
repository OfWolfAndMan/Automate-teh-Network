# Thin harness around the pinned toolchain. README explains what the repo is; this file
# only makes the commands identical on every machine, including CI.

PY ?= python3

.PHONY: help setup inventory preflight lint syntax scrub test

help:
	@printf '%-12s %s\n' \
	  setup     "install the pinned ansible-core and collections" \
	  inventory "parse and graph the lab inventory" \
	  preflight "run the preflight gates (needs a vault password)" \
	  syntax    "ansible-playbook --syntax-check over playbooks/" \
	  lint      "yamllint + ansible-lint + syntax-check" \
	  scrub     "SHIELD gate: fail if a credential, address or identifier would publish" \
	  test      "the whole harness, in order"

setup:
	$(PY) -m pip install --quiet -r requirements.txt
	ansible-galaxy collection install -r requirements.yml -p ./collections

inventory:
	ansible-inventory -i inventories/lab/hosts.yml --graph

preflight:
	ansible-playbook playbooks/preflight.yml --ask-vault-pass

syntax:
	@set -e; for f in playbooks/*.yml; do echo "  $$f"; \
	  ansible-playbook --syntax-check -i inventories/lab/hosts.yml "$$f" >/dev/null; done; \
	  echo "  syntax ok"

lint: syntax
	yamllint -f parsable -c .yamllint.yml .
	ansible-lint playbooks/ || true

scrub:
	$(PY) tools/shield/sanitize.py --check .

test: scrub inventory syntax
	@echo "harness ok"
