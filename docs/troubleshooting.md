# Troubleshooting

The errors below account for almost every first attempt. Each entry is the message you
actually see, why it happens, and what to do. Search this page before searching the internet:
these are the failures this repository produces, not the general population.

---

## Installing the tools

### `No matching distribution found for ansible-core==2.21.6`

**Why.** `pip` cannot find that exact version on the package index it is using. Either the
version does not exist (a typo, or a version newer than the index carries), or a proxy is
blocking PyPI.

**Fix.** Check what is available:

```bash
python3 -m pip index versions ansible-core | head -3
```

If the version in `requirements.txt` is not listed, the pin is wrong — change it to one that
is, rather than removing the pin. If the list is empty or the command errors, you are behind
a proxy: set `PIP_INDEX_URL` to your mirror and try again.

> This is not hypothetical. An earlier revision of this repository pinned 2.22.0, a version
> PyPI does not publish. It installed on the author's machine from a cache and failed on
> every clean runner. A pin you have not installed with `pip` is a guess.

### `ansible: command not found` after `make setup`

**Why.** `pip install --user` puts binaries somewhere your shell does not search.

**Fix.** Either use a virtual environment, or add the user binary directory to your path:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

The rest of this repository's commands assume `ansible` is on your `PATH`.

---

## Collections and modules

### `ERROR! couldn't resolve module/action 'cisco.ios.ios_config'`

**Why.** Collections are not installed, or Ansible cannot see where they are. Collections do
not come with `pip install ansible-core`; they are separate.

**Fix.**

```bash
ansible-galaxy collection install -r requirements.yml -p ./collections
export ANSIBLE_COLLECTIONS_PATH="$PWD/collections"
```

The export matters. Ansible looks in a few standard places and in `./collections` **only when
that path is configured**. If the playbook still cannot find the module, run
`ansible-galaxy collection list` and confirm `cisco.ios` appears.

### `ERROR! couldn't resolve module/action 'community.docker.docker'`

Same cause, different collection. It is needed only by the container exercise;
`requirements.yml` already lists it.

---

## Vault and credentials

### `Attempting to decrypt but no vault secrets found`

**Why.** A playbook read an encrypted file and you did not supply the password.

**Fix.** Add `--ask-vault-pass` to the command. If you would rather not type it each time,
put the password in a file (never in the repository) and pass
`--vault-password-file ~/.ansible-vault-pass`.

### `vault_ansible_password is empty`

**Why.** Preflight's own assertion. The vault file is missing, or exists but still holds the
template's placeholder values.

**Fix.**

```bash
cp inventories/lab/group_vars/all/vault.yml.example inventories/lab/group_vars/all/vault.yml
# edit the values, then:
ansible-vault encrypt inventories/lab/group_vars/all/vault.yml
```

### `echo 'password' > file` seemed fine, but git wants to commit it

**Why.** `.gitignore` excludes `inventories/*/group_vars/all/vault.yml`, not every file you
might create. Name the file as the template does, or check `git status` before committing.

---

## Running playbooks

### `The module interpreter '/usr/bin/env python2  # comment' was not found`

**Why.** A configuration file value swallowed the comment after it. Ansible's `.cfg` format
has **no inline comments**: everything after `=` is the value.

**Fix.** Move the comment onto its own line:

```ini
interpreter_python = auto_silent
# network_cli needs no remote interpreter
```

### `sudo: not found`

**Why.** `become: true` asks the machine for root through `sudo`. A minimal container has no
`sudo`.

**Fix.** For a container running as root, disable become for that host in the inventory:

```yaml
        web1:
          ansible_become: false
```

Connection variables in the inventory win over the `become:` keyword in the play, which is
why this is set per host rather than edited into the playbook.

### `ansible_network_os / ansible_connection missing`

**Why.** Preflight's assertion. The host is in the inventory but not in a platform group
(`cisco_ios`, `cisco_nxos`, `arista_eos`), so Ansible does not know which dialect to speak.

**Fix.** Add the host to the right group in `inventories/lab/hosts.yml`.

### `fatal: [r1]: FAILED! => {"msg": "Failed to connect to the host via ssh: ..."}`

The four usual causes, in order of likelihood:

| Message contains | Cause | Fix |
|------------------|-------|-----|
| `Permission denied (publickey,password)` | wrong credentials, or the vault value is a placeholder | check the vault values; for a device, check the username |
| `Connection timed out` / `No route to host` | the address is wrong or unreachable | `ping` it; confirm you are on the right network |
| `Authentication or authorization failure` | device rejected the login after connecting | confirm the device allows SSH (not only Telnet) for that user |
| `Timeout (12s) waiting for privilege escalation` | `become` is on but the device has no enable password | set `ansible_become: false` for that host, or supply the enable password |

### `changed=1` on every single run

**Why.** Something in the playbook is not idempotent — usually a `command:` or `shell:` task
without a `creates:` guard, or a template that renders a timestamp.

**Fix.** Find the task reporting `changed` and add the check that would let the module skip
it. `command:` accepts `creates:` (run only if this file is absent) and `changed_when:`
(decide for yourself whether a change occurred). The whole point of the exercise is that the
second run says `changed=0`.

---

## The container exercise

### `permission denied while trying to connect to the Docker daemon socket`

**Fix.** Add yourself to the `docker` group and start a new login session:

```bash
sudo usermod -aG docker "$USER"
```

Then log out and back in. (`newgrp docker` works for the current shell.)

### `docker: Error response from daemon: Conflict. The container name "/lab-web1" is already in use`

**Fix.** `docker rm -f lab-web1`, then run the exercise again.

---

## Linting and CI

### `yamllint` complains about `.github/workflows/ci.yml` (`truthy value should be ...`)

**Why.** YAML 1.1 reads the key `on:` as boolean true, so every GitHub workflow trips that
rule. It is a property of the format, not a mistake in the file.

**Fix.** None needed — `.yamllint.yml` already ignores `.github/workflows/`. If you copied
the configuration elsewhere, copy that ignore too.

### `ansible-lint` reports `package-latest`

**Why.** A task installs with `state: latest`. That is sometimes deliberate — one playbook in
this repository exists to upgrade packages.

**Fix.** Justify it in place: `# noqa: package-latest`. If you cannot justify it, use
`state: present`.

### CI fails at `Install the pinned toolchain` but the same commands work locally

**Why.** Your machine and the runner have different package indexes, Python versions, or
caches. This is the failure mode that produced the `2.22.0` incident above.

**Fix.** Reproduce the job rather than reasoning about it:

```bash
docker run --rm -v "$PWD:/w" -w /w python:3.12-slim pip install -r requirements.txt
```

If that fails, the problem is in `requirements.txt`, not in CI.
