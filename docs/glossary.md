# Glossary

One sentence each, in the order you are likely to meet them.

| Term | What it means here |
|------|--------------------|
| **Ansible** | a program that connects to machines and makes them match a description you write |
| **ansible-core** | Ansible itself, without the vendor modules; this repository pins version 2.21.6 |
| **collection** | a bundle of modules for one vendor or purpose (`cisco.ios`, `arista.eos`, `ansible.posix`); installed with `ansible-galaxy`, not with `pip` |
| **module** | the thing that does one job on a machine — `ansible.builtin.package` installs software, `cisco.ios.ios_l2_interfaces` configures switch ports |
| **FQCN** | "fully qualified collection name": the three-part module name `namespace.collection.module`, e.g. `cisco.ios.ios_config`; used so two collections can never collide |
| **task** | one instruction in a playbook, usually one module call |
| **play** | a block of tasks that apply to one group of hosts |
| **playbook** | a YAML file of plays, run top to bottom |
| **role** | a reusable bundle of tasks, defaults and templates with a fixed directory layout; `roles/network_backup` is one |
| **inventory** | the list of machines Ansible may contact, and how to reach each one |
| **group** | a label in the inventory (`routers`, `cisco_ios`) used to select which machines a play applies to |
| **host_vars / group_vars** | per-machine and per-group settings, in files named after the host or group |
| **connection plugin** | how Ansible reaches a machine: `ssh` for servers, `network_cli` for device command lines, `httpapi` for a device's web API, `community.docker.docker` for a container |
| **network_cli** | the connection that logs into a switch or router over SSH and speaks its CLI |
| **ansible_network_os** | the inventory variable that tells the connection which vendor's dialect to expect (`cisco.ios.ios`, `arista.eos.eos`) |
| **idempotent** | running it again changes nothing, because the description is already satisfied |
| **converged** | the machine now matches the description; usually shown by `changed=0` on a second run |
| **gathered / state=gathered** | a module mode that *reads* a device's current configuration into structured data instead of changing it |
| **check mode** | `--check` — report what would change without changing it |
| **vault** | Ansible's file encryption; `ansible-vault encrypt file.yml` turns a file of secrets into unreadable text |
| **fact** | a piece of information Ansible learned about a machine (its interfaces, its OS version) |
| **handler** | a task that only runs when something it watches reports a change, e.g. "reload nginx" |
| **lint / ansible-lint** | a checker that reads your playbooks and complains about risky or unclear constructs |
| **yamllint** | a checker for YAML formatting |
| **compliance policy** | one rule a device's configuration must satisfy, written as data in `policies/compliance.yml` — "every vty line accepts only SSH" |
| **JSON Schema** | a standard way to describe what valid data looks like; `policies/compliance.schema.json` rejects a malformed policy before it is used |
| **filter plugin** | a Python function Ansible can call inside `{{ }}`; `compliance_check` is this repository's |
| **fixture** | a saved sample of real data used for testing; `tests/fixtures/` holds sanitised device configurations |
| **scrub** | this repository's own tool (`tools/shield/sanitize.py`) that replaces credentials and addresses with safe placeholders before they can be published |
| **address plane** | the three ranges this repository allows: internal `10.0.0.0/16`, external `198.18.0.0/15`, documentation RFC 5737 |
| **RFC 1918 / RFC 5737 / RFC 2544 / RFC 3849** | the standards that reserve those ranges for private use, documentation examples, benchmarking, and IPv6 examples respectively |
| **type-5 / type-7** | two ways Cisco stores passwords in a configuration: type-5 is a hash (crackable), type-7 is reversible obfuscation |
| **containerlab** | a tool that builds a virtual network of routers and switches from Docker images |
| **cEOS** | Arista's containerised switch operating system; the licence is granted per Arista account, which is why this repository does not ship it |
| **CI** | continuous integration: the service that runs the checks on every push |
| **fixture / artifact** | a fixture is an input kept for tests; an artifact is output produced by a run (`artifacts/` is git-ignored) |
