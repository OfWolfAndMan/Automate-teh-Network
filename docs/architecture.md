# Architecture

What this repository is, and what it refuses to be.

## Shape

```text
ansible.cfg                 toolchain behaviour: inventory, collections, timeouts
requirements.txt            pinned ansible-core, control-node libraries, lint and test tooling
pyproject.toml              pytest and ruff configuration
requirements.yml            pinned collections
inventories/lab/            the only inventory: hosts, group_vars, host_vars
playbooks/network/          device-facing: backup, compliance, facts, interfaces, l2, hardening, show
playbooks/linux/            host-facing: baseline, update_packages, web
roles/network_backup/       one role, three platform task files
roles/network_compliance/   policy gate, evaluation, report
policies/                   compliance policies as data + their JSON Schema
plugins/filter/             compliance_check — the policy engine, stdlib Python
examples/python/            teaching programs for when Ansible is not enough
tools/shield/               the containment scrub
tools/gen_index.py          README inventory generated from playbook metadata
lab/                        containerlab topology + the container target
scripts/e2e_*.sh            the two lab layers, and the offline compliance and show runs
tests/                      pytest, offline inventories, and fixtures (read-only device output)
docs/                       the standards this repository is held to
```

## The three decisions that shape everything

1. **Intent, not rendered configuration.** The 2017 tree built a whole device
   configuration with Jinja and pushed it with `lines:`. That cannot answer "is the device
   already correct?", which is the only question that matters on the second run. Every
   device-facing playbook here declares state through a resource module
   (`ios_interfaces`, `ios_l2_interfaces`, `ios_snmp_server`, …), and the lab asserts
   `changed=0` on a second pass. Compliance is the read-only half of the same idea: policy
   is data, the device's configuration is evidence, and the answer is a report rather than
   a push.

2. **One role, dispatched on the platform the inventory already declares.** Four parallel
   role trees that differ only in a module name duplicate the platform fact the inventory
   already carries.

3. **Addresses and credentials are a machine-checked standard, not a convention.**
   `docs/addressing-and-placeholder-standard.md` defines three address planes and the
   placeholder scheme; `tools/shield/sanitize.py` enforces both, and CI fails on a
   violation. Structure that is only documented drifts; structure that is checked does not.

## What runs where

| Layer | Needs | Proves |
|-------|-------|--------|
| `make test` | python, ansible-core | scrub, inventory parse, syntax, README index, pytest, compliance and show.yml against the fixtures |
| `make e2e-linux` | docker | a playbook converges and is idempotent (pass 2 changed=0) |
| `make e2e-network` | containerlab + vendor images | the same, against a fabric |

Layer 2 is skipped, loudly, when the images are absent (exit 77). A skip is reported as a
skip in CI rather than counted as a pass — a fabric test that did not run is not evidence.

## Rules the repository is held to

- A playbook says when it was executed and against what, or it says it was never executed.
  `tools/gen_index.py` refuses an unknown status and CI fails if the README is stale.
- Nothing published carries a real credential, a real address or a real name.
- Retirements are recorded with reasons in `docs/retirements.md`; git keeps the text.
