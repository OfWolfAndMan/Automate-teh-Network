> **Status (2026-11-11): modernized, unpushed.** The 2017-2024 corpus has been contained,
> re-laid-out and rewritten on branch `modernize/phase-0`. What is here now:
>
> - `playbooks/network/` and `playbooks/linux/` — intent-based playbooks on current
>   collections (`cisco.ios` 11.6, `cisco.nxos` 13.0, `arista.eos` 12.3)
> - `roles/network_backup/` — one role replacing four per-OS role trees
> - `inventories/lab/` — the three-plane address scheme, credentials from a vault
> - `tools/shield/` — the containment scrub that CI enforces
> - `lab/` + `scripts/e2e_*.sh` — the substrate and its idempotence assertions
> - `docs/` — the address/placeholder standard, the architecture, and every retirement
>
> Rules in `CONTRIBUTING.md`. The legacy playbooks that this replaces are gone; each
> removal and its reason is in `docs/retirements.md`. Device configuration dumps under
> `Playbooks/Network_Vendors/` are retained deliberately as test fixtures.


# Ansible Playbooks (Linux and Network Vendors)
## Version 1.0

An array of Ansible playbooks in the making for the benefit of automating all the things (Or those that should be).

Built in python 2.7, although will be migrated to python 3.6 soon due to nearing EOS state of 2.7.

These playbooks are constructed in a manner that aligns as close to "Best practice" as possible. For more details on Ansible best practice file structure, visit Ansible's website, or view the "playbook-build-example" file.

**Environment variables**
The following should be set in your environment file (i.e. .bashrc) to ensure proper usage:
- NETWORK_DOMAIN_NAME

**Variable Precedence**

It is important to know the variable precedence to understand how to structure each playbook. Below is the precedence as of Ansible 2.3.x

 | PRECEDENCE |      VARIABLE NAME      |           COMMON LOCATION          |
 |------------|-------------------------|------------------------------------|
 | 1.         | Inventory Vars          | Inventory file [all:vars]          |
 | 2.         | Inventory Group_Vars    | Inventory file [group:vars]        |
 | 3.         | Inventory Host_Vars     | Inventory file [host:vars]         |
 | 4.         | Playbook All vars       | /vars/                             |
 | 5.         | Playbook Group_Vars     | /group_vars/                       |
 | 6.         | Playbook Host_Vars      | /host_vars/                        |
 | 7.         | Host Facts              | Playbook -  gather_facts module    |
 | 8.         | Registered Vars         | Playbook - register module         |
 | 9.         | Set_Facts               | Playbook - set_fact module.        |
 | 10.        | Play vars               | Defined within playbook            |
 | 11.        | Play vars_prompt        | Defined within playbook            |
 | 12.        | Play vars_files         | Defined within playbook            |
 | 13.        | Role and include vars   | /roles/ and within playbook        |
 | 14.        | Block vars              | Playbook - block module            |
 | 15.        | Task vars               | Defined within playbook            |
 | 16.        | Extra vars              | --extra-vars - adhoc command       |

**Network Vendors support**

The following is a list of the network vendors that are currently or will be included in the future with these playbooks.

 |  Vendor/OS      |   Status      |
 |-----------------|---------------|
 | Cisco IOS/XE    | Available     |
 | Cisco IOS-XR    | Not Projected |
 | Cisco NX-OS     | Projected     |
 | Arista vEOS     | In Progress   |
 | Cumulus VX      | In Progress   |
 | HP (Any)        | Not Projected |
 | Brocade (Any)   | Unsure        |
 | Avaya ERS       | Available     |
 | Avaya VSP       | Projected     |
 | Junos           | Projected     |
 | Riverbed RiOS   | Desired       |
 | Citrix Netscaler| Desired       |

- Available: A playbook exists

- Not Projected: Nothing completed and nothing planning to be done

- Projected: Plans to be written, but not a current task

- In progress: In a particular stage of development

- Unsure: Thoughts of writing a playbook, but unsure if necessary

- Desired: Little support from the community. Would require extensive efforts on the backend.

**Playbook Examples**

- Template rendering of network configurations

- SNMP facts

- Show output parsing to a SQL file (Using ntc-ansible's TextFSM feature)

- Roles for modular Playbook implementation

**Future Vision Feature sets**

- NAPALM playbooks
 
  + Diff capabilities

  + Configuration pushes

  + Configuration Backups

- Topology maps

- Further development of roles

- AWX OR Ara integration. Not sure which yet

## Playbooks

<!-- INDEX:START -->

| Playbook | Purpose | Status | Verified | Environment |
|----------|---------|--------|----------|-------------|
| `playbooks/linux/baseline.yml` | Baseline a Linux host | **verified** | 2026-11-11 | ansible-core 2.22.0, community.docker, python:3.12-slim |
| `playbooks/linux/update_packages.yml` | Update packages | **unverified** | 2026-11-11 | ansible-core 2.22.0; syntax-check only |
| `playbooks/linux/web.yml` | Serve a loopback-only TLS page | **unverified** | 2026-11-11 | ansible-core 2.22.0; syntax-check only |
| `playbooks/network/backup.yml` | Back up device configurations | **unverified** | 2026-11-11 | ansible-core 2.22.0; syntax-check only — no fabric images on the build host |
| `playbooks/network/facts.yml` | Gather structured interface facts | **unverified** | 2026-11-11 | ansible-core 2.22.0; syntax-check only |
| `playbooks/network/hardening.yml` | Remove factory-default SNMP communities | **unverified** | 2026-11-11 | ansible-core 2.22.0; syntax-check only |
| `playbooks/network/interfaces.yml` | Converge L3 interface intent | **unverified** | 2026-11-11 | ansible-core 2.22.0; syntax-check only |
| `playbooks/network/l2.yml` | Converge L2 interface intent | **unverified** | 2026-11-11 | ansible-core 2.22.0; syntax-check only |
| `playbooks/network/show.yml` | Run a command and parse it | **unverified** | 2026-11-11 | ansible-core 2.22.0; syntax-check only |
| `playbooks/preflight.yml` | Preflight — inventory, address plane and credential gate | **verified** | 2026-11-11 | ansible-core 2.22.0; empty vault fails, template vault fails, encrypted vault passes 7/7 |

_10 playbooks. Generated by `tools/gen_index.py`._

<!-- INDEX:END -->
