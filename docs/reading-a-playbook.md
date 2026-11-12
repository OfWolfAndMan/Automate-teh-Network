# Reading a playbook

One file, annotated. After this, the rest of `playbooks/` should read easily.

Open `playbooks/preflight.yml`. It is short and it does something you can watch, which makes
it a good first specimen. Below is the file with an explanation under each part.

```yaml
---
```

Three dashes mean "this is one YAML document". Ansible files almost always start with it.
It is not decoration: a file with two such markers is read as two documents, and the second
one is usually a mistake.

```yaml
- name: Preflight — inventory, address plane and credential gate
  hosts: network
  gather_facts: false
  connection: local
  any_errors_fatal: true
```

The dash starts a list; each item in the list is one **play**. The keys inside it:

| Key | Meaning |
|-----|---------|
| `name` | a label, printed as a heading when the playbook runs. Write it for a human. |
| `hosts` | which inventory group this play applies to. `network` is a group in `inventories/lab/hosts.yml` |
| `gather_facts` | `false` stops Ansible asking each device for its OS, memory and so on. It saves time and, for a check that contacts nothing, it is the honest setting |
| `connection` | `local` means "run these tasks on the machine I am typing on", not on the device |
| `any_errors_fatal` | stop the whole play at the first failure, instead of carrying on with the remaining hosts |

```yaml
  tasks:
    - name: Every host declares a network platform
      ansible.builtin.assert:
        that:
          - ansible_network_os is defined
          - ansible_network_os | length > 0
          - ansible_connection is defined
        fail_msg: "{{ inventory_hostname }}: ansible_network_os / ansible_connection missing"
        quiet: true
```

`tasks:` is a list. Each item is one task, and a task is one module call.

- `ansible.builtin.assert` is the module. The `ansible.builtin` prefix says it ships with
  Ansible itself rather than with a vendor collection.
- `that:` is a list of conditions, each of which must be true. If any is false, the task
  fails.
- `ansible_network_os` is a variable. Variables come from the inventory, from `group_vars`,
  or from the command line. Here it comes from the platform groups in `hosts.yml`.
- `{{ inventory_hostname }}` is a placeholder: Ansible substitutes the current host's name
  into the message before printing it.
- `quiet: true` suppresses a line of noise per host. Not required; pleasant.

Why this task exists: if a host is missing `ansible_network_os`, Ansible cannot know which
vendor's dialect to speak, and the failure later would be cryptic. This task converts a
cryptic failure into a sentence.

```yaml
    - name: Every address sits inside a declared plane
      ansible.builtin.assert:
        that:
          - (ansible_host is match('10\\.0\\.'))
            or (ansible_host is match('198\\.18\\.'))
            ...
```

`is match(...)` is a test — Ansible's name for a yes/no check on a value. The doubled
backslashes are how you write a literal dot in this string: `10\\.0\\.` matches addresses
beginning `10.0.`.

The condition is true if the address starts with one of the allowed prefixes. This is the
repository's address rule, enforced by a machine instead of by a reviewer's memory.

```yaml
    - name: Credentials must resolve from the vault, never from the inventory
      ansible.builtin.assert:
        that:
          - vault_ansible_password is defined
          - vault_ansible_password | length > 0
        fail_msg: >-
          vault_ansible_password is empty. Copy group_vars/all/vault.yml.example to
          vault.yml, fill it, and encrypt it with ansible-vault before running anything.
```

`| length > 0` is a filter: the pipe takes the value on the left and passes it through the
named operation. `fail_msg` is what the user sees on failure, and it should say what to do —
not merely that something is wrong.

```yaml
    - name: Preflight summary
      ansible.builtin.debug:
        msg: >-
          {{ inventory_hostname }}: {{ ansible_network_os }} at {{ ansible_host }}
          via {{ ansible_connection }}
```

`debug` prints a message. `>-` is YAML's "fold these lines into one, keeping the newlines
out", so a long message can be written across lines without odd spacing in the output.

---

## The same ideas in a playbook that changes things

`playbooks/linux/baseline.yml` is the one the container exercise runs. Two tasks from it:

```yaml
    - name: Install baseline packages
      ansible.builtin.package:
        name: "{{ baseline_packages }}"
        state: present
```

`package` is a generic module: it works out whether the machine uses `apt`, `dnf` or
something else. `state: present` means "installed" — as opposed to `latest`, which means
"installed and upgraded", and which is a decision with consequences.

```yaml
    - name: Deploy the login banner
      ansible.builtin.copy:
        content: "{{ baseline_motd }}"
        dest: /etc/motd
        mode: "0644"
```

`copy` writes content to a file. Note what is *not* here: no shell command, no `echo >`,
no conditional "if the file already has the right text". The module compares what is there
with what you asked for, and reports `changed` only when it had to act. That is where
idempotence comes from — not from cleverness in the playbook, but from modules that know how
to check.

---

## Reading order for the rest

| File | What it teaches |
|------|-----------------|
| `playbooks/preflight.yml` | assertions, variables, `connection: local` |
| `playbooks/linux/baseline.yml` | modules that converge a machine, and idempotence |
| `playbooks/linux/web.yml` | a handler (`notify`), generating a certificate on the target, and why secrets are not committed |
| `roles/network_backup/tasks/main.yml` | a role, `include_tasks`, and dispatch on a variable |
| `playbooks/network/interfaces.yml` | describing desired state instead of commands |
| `playbooks/network/hardening.yml` | asserting that something is *absent* |

One habit: when a module name is unfamiliar, ask Ansible rather than a search engine.

```bash
ansible-doc cisco.ios.ios_config
ansible-doc -l cisco.ios | grep interfaces
```

The first prints the manual page. The second lists every module in a collection. Both read
from the collections you actually installed, which is more reliable than any tutorial
written against a different version.
