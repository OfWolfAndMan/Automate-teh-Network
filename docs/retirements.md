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
| `tests/fixtures/backups/**` (moved from `Playbooks/Network_Vendors/Universal-Backup/backup/`) | the only fixtures this repository has. A backup role without fixtures is a claim without a test (reviewer ruling, 2026-11-11). |
| `tests/fixtures/configs/management-SW*.cfg` (moved from `Playbooks/Network_Vendors/configs/`) | generated-config fixtures, sanitised, used to exercise parsing and diffing |

These are data, not code: they are inputs to tests, and they are excluded from the
"executed or it is not current" rule because they are not instructions to run.

## Absorbed: Network-Automation-Mini-Course (2019–2021)

A separate repository, the companion code for a video course: a "config compliance
service" plus the scripts from individual lessons. It was ported here fresh, not merged
with history, because its history carries hard-coded credentials and addresses outside the
declared planes, and a merge would publish both again.

As published, its pipeline could not start: `deploy-lab.py` and `destroy-lab.py` import
`EVE_NG.provisioning` and `EVE_NG.devices`, which were never committed, and `main.py`
reports on a "verified devices" list nothing in the repository ever populates.

### Carried over

| Course file | Successor | What changed |
|-------------|-----------|--------------|
| `main.py`, `shared/resources.py::parse_policy`, `pre-checks.py` | `playbooks/network/compliance.yml`, `roles/network_compliance/`, `plugins/filter/compliance.py` | collection by `network_backup`, not a thread per device joined one at a time; a stdlib parser, not CiscoConfParse v1; a report plus a failed host, not a text file |
| `APIs/config_policies.yml` | `policies/compliance.yml` | readable `id`s instead of random hex; `transport input ssh` widened to `(ssh\|none)`; VTP v3 restated as `vtp mode (off\|transparent)`; `state: absent` added |
| `APIs/Schemas/config_policy_validators.yml`, `APIs/validators.py` | `policies/compliance.schema.json` | JSON Schema enforced by `ansible.utils.validate`, not Cerberus |
| `Classes/objects.py`, `uncategorized/netmiko_async.py` | `examples/python/device.py`, `concurrent_show.py` | no login at import; credentials from the environment; concurrency that is actually concurrent |
| `shared/regex-prototype.py` | `examples/python/access_ports.py` | one block at a time, named groups; runs against the fixtures |
| `inventory/inventory_parser.py`, `inventory/config/Sw{1,2}.txt` | `examples/python/show_version_csv.py`, `tests/fixtures/show/` | no run at import; stack members kept; captures sanitised |
| `shared/resources.py::get_dbentries_postgres` | `examples/python/inventory_db.py` | SQLite, placeholders, an identifier allow-list, and the real Ansible inventory as data |

### Not carried over

| Course file | Reason |
|-------------|--------|
| `APIs/app.py`, `APIs/lab_devices.yml`, `Schemas/lab_devices_validators.yml` | a Flask inventory API, run with `debug=True` on `0.0.0.0` — the Werkzeug debugger executes code for anyone who can reach it. Its POST handlers wrote to a different path than they read. `inventories/lab/` is the inventory now. |
| `EVE_NG/*`, `deploy-lab.py`, `destroy-lab.py`, `tests/test_provisioning.py` | EVE-NG lab provisioning with the default `admin`/`eve` login; `EVE_NG/lab_provisioning.py` ran its whole flow on import. containerlab (`lab/`) is the substrate now. |
| `configTemplates/**`, `render_templates.py`, `test-render.py`, `tests/test_templates.py` | whole-config Jinja rendering, the pattern this repository retired in Phase 2 (`docs/architecture.md`). `initial.j2` carried a plaintext `enable secret`. Eight of the twelve templates were empty files. |
| "Disable LLDP Globally" (EOS policy) | LLDP is how a fabric verifies its own cabling. Turning it off everywhere is not a baseline. |
| `shared/zmq_connect.py`, `message_test.py` | an unfinished request/reply sketch; `pyzmq` was never in `requirements.txt` |
| `shared/resources.py::send_slack`, `load_api_data`, `thread_update` | a NetBox poller that sent Slack messages, built on `slackclient` (replaced by `slack_sdk` in 2020); it indexed a `requests.Response` as a dict, so it could not have run |
| `tests/test_main.py` | asserted properties of hard-coded lists and dictionaries; nothing under test |
| `requirements.txt` | 23 packages, 22 unpinned, about half never imported (jupyterlab, sphinx, nornir, flask_login, psycopg2, …) |
| `Makefile`, `.flake8`, `.bandit`, `pyproject.toml` | targets wrote into `Logs/` and `compliance/`, which did not exist; `make`, ruff and pytest configuration here replace them |
| `sample-report-25-08-2019_20:14:00.txt`, `Workflow.png` | output and a diagram of the retired pipeline |
| `README.md` | described the service above |

## Absorbed: NotLayer3-NetworkAutomation (2020)

The earlier, 2020 edition of the same course: Python lessons plus a "final project" that is
the compliance service the mini-course later refined. Ported fresh, not merged, for the
same reason: its files and history carry plaintext device passwords and real, routable
addresses.

Most of it was already superseded by the mini-course work above. Three pieces were not.

### Carried over from NotLayer3

| Course file | Successor | What changed |
|-------------|-----------|--------------|
| `runner.py get-cdp-data`, `utils.parse_outputs` | `playbooks/network/show.yml` with `show_save=true` | any command, not only CDP; parsed by `ansible.utils.cli_parse` and saved as JSON per host; a saved capture can be parsed offline (`show_text_file`), which is how it is now tested |
| `advanced_python/comprehensions.py` | `examples/python/comprehensions.py` | `ipaddress` membership instead of `startswith("192.168.")`; works over the real inventory |
| `basic-python/connections.py`, `utils.get_config` error handling | `examples/python/connect_with_logging.py` | named Netmiko exceptions instead of a bare `except:`; logging configured in `main()`, not at import |

### Not carried over from NotLayer3

| Course file | Reason |
|-------------|--------|
| `main.py`, `pre-checks.py`, `utils.py` (compliance parts), `APIs/` (`app.py`, `data/policies.yml`), `Final Project Details/Required Data`, `Makefile` | the compliance service, superseded by `playbooks/network/compliance.yml`. Its six policies are the mini-course's six, one-for-one; see above for how each was carried or corrected. |
| `APIs/data/devices.yml` | five devices, each with the same plaintext password; `inventories/lab/` and the vault replace it |
| `advanced_python/classes.py`, `advanced_python/regex.py` | covered by `examples/python/device.py` and `access_ports.py` |
| `advanced_python/template-renderer.py`, `configTemplates/**` | whole-config Jinja rendering, retired in Phase 2 |
| `advanced_python/documenting.py`, `os-sys.py` | a docstring around a function calling an undefined class, and `print(os.getcwd())`; every example now carries docstrings and type hints |
| `basic-python/variables.py`, `file_mgmt.py`, `my-yam.yml`, `*.txt` | first-week Python (variables, files, YAML) with plaintext passwords and two globally routable public addresses as sample data |
| `log.txt`, `basic-python/log.txt` | 23,966 lines of 2020 connection logs committed by mistake |
| `tests/test_main.py` | a stray `g` on line 15 raises NameError at import, so pytest could not collect it — it never ran |
| `git-basics.txt` | a git cheat sheet; nothing here depends on it |
| `Final Project Details/Postman-install` | CentOS 7 install notes for Postman, for an API that is retired |
| `requirements.txt`, `basic-python/requirements.txt`, `.flake8` | unpinned; replaced by the pinned top-level files and ruff |
