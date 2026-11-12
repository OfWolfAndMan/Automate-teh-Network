# Configuration compliance

The other network playbooks in this repository *change* devices so they match a description.
Compliance asks a different question, and changes nothing: **is each device configured the
way policy says it must be?** The answer is a report, and a failed host for every device
that is not.

```bash
# offline, against the saved fixture configurations — no device, no vault (about ten seconds)
ansible-playbook -i tests/compliance/hosts.yml playbooks/network/compliance.yml

# against the lab: collect each running configuration first, then check it
ansible-playbook playbooks/network/compliance.yml --ask-vault-pass
```

Either way, the report lands in `.artifacts/compliance/report.md` (for people) and
`report.json` (for anything that consumes it). Both are git-ignored outputs.

## What you should see offline

Seventeen hosts are checked. Thirteen pass. Four fail, and the play stops for those four:

```text
fatal: [SW1]: FAILED! => ... SW1: 1 of 6 policies violated — no-domain-lookup
```

That is correct, not a fault in the playbook. The four switch configurations in
`tests/fixtures/backups/` set `ip domain-name` but never `no ip domain lookup`, so a mistyped
command on those switches is sent to DNS as a hostname. The report says the same in a table.

To get the report without the failure, add `-e network_compliance_fail_on_violation=false`.

## How it works

```text
policies/compliance.yml ──► schema gate ──► compliance_check filter ──► report ──► assert
                            (JSON Schema)    (one per host)              (once)    (per host)
running config ─────────────────────────────────┘
```

1. **Load and validate the policies.** `policies/compliance.yml` is checked against
   `policies/compliance.schema.json` with `ansible.utils.validate`. A misspelt key, a missing
   description or an unknown platform stops the run before any device is judged by it.
2. **Get the running configuration.** By default the `network_backup` role collects it into
   `.artifacts/configs/<host>.cfg`. Set `network_compliance_collect=false` to check files
   already on disk.
3. **Evaluate.** The `compliance_check` filter (`plugins/filter/compliance.py`) parses the
   configuration and tests every policy that applies to the host.
4. **Report, then fail.** The report is written first, so a failing run still leaves the
   evidence behind.

## Writing a policy

A policy is a few lines of YAML in `policies/compliance.yml`:

```yaml
- id: ssh-only-vty
  description: VTY lines accept SSH or nothing, never telnet
  platforms: [ios]
  parent: "line vty .*"
  config: "transport input (ssh|none)"
```

| Key | Required | Meaning |
|-----|----------|---------|
| `id` | yes | lower-case, hyphenated; shown in the report and the failure message |
| `description` | yes | why the policy exists, in one sentence |
| `platforms` | yes | any of `ios`, `nxos`, `eos` — the last part of `ansible_network_os` |
| `groups` | no | inventory groups it applies to; omit for every host on the platform |
| `parent` | no | selects blocks such as `line vty 0 4`; omit for a top-level line |
| `config` | yes | the line that must be present (or absent) |
| `state` | no | `present` (the default) or `absent` |

### The matching rules

**Every pattern is a regular expression that must match the whole line.** Indentation is
ignored and repeated spaces count as one. So `ip ssh version 2` matches exactly that line,
and not `ip ssh version 2 extra`. Use `( .*)?` when trailing words should be allowed.

| `parent` | `state` | Compliant when |
|----------|---------|----------------|
| — | present | some top-level line matches `config` |
| — | absent | no top-level line matches `config` |
| set | present | at least one block matches `parent`, **and every one of them** has a child matching `config` |
| set | absent | no block matching `parent` has a child matching `config` |

The "every block" rule matters. IOS has `line vty 0 4` *and* `line vty 5 15`, and a policy
about "the vty lines" is satisfied only when both comply.

Comment lines (`!`) and banner text are ignored, because neither is configuration.

### Two mistakes worth knowing about

- **Asserting a line the device never prints.** `no transport input telnet` is how you
  remove telnet, but it never appears in a running configuration, so a policy requiring it
  fails on every device forever. Assert what the device *shows* (`transport input ssh`), or
  state the bad line `absent`.
- **A space after `snmp-server community`.** The scrub (`make scrub`) reads whatever follows
  that phrase as a community string and replaces it. Write `snmp-server community[ ]...`
  instead; it matches the same lines.

## Testing a change

```bash
make pytest       # the filter's rules, and the shipped policies against every fixture
make compliance   # the playbook end to end: right hosts fail, report stable, schema enforced
```

When a policy change alters which fixtures pass, update the expectations in
`tests/test_compliance.py` and `scripts/e2e_compliance.sh`. Work out the new result from
the fixture itself (`grep` is enough), then confirm the engine agrees. Copying the engine's
output into the test would prove nothing.

## Where this came from

This replaces the compliance service in the 2019–2021 *Network-Automation-Mini-Course*: a
Flask API serving policies and devices, Cerberus validation, CiscoConfParse, and a text
report. The question it asked was the right one. `docs/retirements.md` records what was not
carried over, and why.
