# Retirements

Every file removed in Phase 2, and why. Git history keeps the text; this page keeps the
reason, which is the part a future reader cannot recover from a diff.

## Removed: playbooks and roles (superseded)

| Removed | Reason | Successor |
|---------|--------|-----------|
| `Playbooks/Network_Vendors/Universal-Backup/{main.yml,roles/}` | four role trees (ios/eos/nxos/cumulus) identical except for the module name; `connection: local` with `provider:` dicts, both deprecated since 2.5 | `roles/network_backup` — one role, three task files, dispatched on `ansible_network_os` |
| `Playbooks/Network_Vendors/L2switches.yml`, `roles/management/` | rendered an entire device configuration in Jinja and pushed it with `ios_config: lines:`; nothing could be said about whether the device had already converged | `playbooks/network/l2.yml` with `*_l2_interfaces` |
| `Playbooks/Network_Vendors/breakconfig.yml` | free-form `no snmp-server community ...` lines | `playbooks/network/hardening.yml`, declarative `*_snmp_server` |
| `Playbooks/Network_Vendors/ntc-test.yml`, `avaya-test.yml` | `ntc_show_command` from the archived `ntc-ansible` role, with a `template_dir` pointing at a sibling checkout that no longer exists | `playbooks/network/show.yml` using `ansible.utils.cli_parse` |
| `Playbooks/Network_Vendors/show_output.yml`, `L2switches` vars, `group_vars/Network-Physical.yml` | same template-push pattern, one host group each | the declarative playbooks above |
| `Playbooks/Linux/{update_packages.yml,roles/nginx,roles/tasks,hosts}` | `ansible_ssh_pass` inline in inventory, a committed TLS keypair, no OS-family check | `playbooks/linux/{update_packages,web}.yml`; the key now exists only on the host that generates it |
| `Playbooks/Linux/PostGRE-Tables.yml`, `files/NetworkTables.sql` | loaded a 2017 schema dump onto a Raspberry Pi; the database and the host are both gone | nothing — record kept here |
| `Development/` | 2018 scratch: a Jinja object demo, snippets, a textfsm parser and its output | the object demo is superseded by resource-module intent; the parser by `cli_parse` |
| `Jenkinsfile` | one stage, calling `myshell.sh`, which has never existed in this repository. It has never run. | `.github/workflows/ci.yml` (Phase 4) |
| `install-environment.sh` | `pip2 install`, then `sudo python setup.py install` of an archived role. An instruction nobody should follow. | `requirements.txt` + `requirements.yml`, pinned |
| `ansible-requirements.txt` | unpinned `ansible`, `napalm`, `textfsm`, `gtextfsm`, `terminal` | `requirements.txt` |
| `Automation-Flow.txt` | ASCII diagram of a flow the repository never implemented | `docs/architecture.md` |
| `tree-structure`, `playbook-build-example` | described a layout the repository did not have | the layout now exists |
| `Data Model Example.png` | 400 KB diagram of a data model with no code behind it in this repository | nothing |

## Removed: retired products (no successor exists)

| Removed | Reason |
|---------|--------|
| `avaya-test.yml` | Avaya's networking line was sold to Extreme Networks in 2017. There is nothing to modernise: the platform's own documentation is no longer published by its vendor. |
| `Cumulus/implement_quagga.yml`, `common.yml`, `update_packages.yml` | Quagga was superseded by FRR, and Cumulus is NVIDIA Cumulus Linux. The playbooks install a routing daemon that is no longer shipped. |

## Retained on purpose

| Retained | Why |
|----------|-----|
| `Playbooks/Network_Vendors/Universal-Backup/backup/**` | the only fixtures this repository has. A backup role without fixtures is a claim without a test (reviewer ruling, 2026-11-11). |
| `Playbooks/Network_Vendors/configs/management-SW*.cfg` | generated-config fixtures, sanitised, used to exercise parsing and diffing |

These are data, not code: they are inputs to tests, and they are excluded from the
"executed or it is not current" rule because they are not instructions to run.
