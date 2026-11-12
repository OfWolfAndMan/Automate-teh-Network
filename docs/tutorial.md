# Your first network automation exercise

This is a guided exercise. If you have never used Ansible, start here. It takes about
thirty minutes, needs no network hardware, and ends with you having changed a machine's
configuration twice and understood every word of the command that did it.

By the end you will be able to answer, without jargon:

- what Ansible is and what a "playbook" actually does
- how Ansible knows which machines to talk to
- why running the same thing twice is the point, not a mistake
- how to point all of this at a real switch or router

---

## What Ansible is, in plain words

Ansible is a program that connects to machines and makes them match a description you
wrote. That is the whole idea.

You write a file listing what you want — "this server has nginx installed", "this switch
has an address on GigabitEthernet1" — and Ansible logs in, compares what is there with what
you asked for, and changes only the difference. If nothing is different, it changes nothing
and says so.

That last property has a name, **idempotence**, and it is the reason this repository exists
in its current shape. Older automation pushed a whole configuration file at a device every
time, which meant a second run looked identical to the first and nobody could tell whether
the device had drifted. Describing *state* instead of *commands* lets Ansible answer the
question "is it already correct?" — and that answer is what makes automation safe to run on
a schedule.

Three words recur, and they are worth fixing now:

| Word | Plain meaning |
|------|---------------|
| **inventory** | the list of machines Ansible is allowed to talk to, and how to reach them |
| **task** | one instruction, e.g. "install these packages" |
| **playbook** | a file of tasks, run in order, against a group of machines from the inventory |

Ansible itself needs nothing installed on the machines it manages for the Linux examples
here — it logs in over SSH and runs commands. Network devices are different: Ansible
connects the way a human would, over SSH or HTTPS, and speaks the device's own command
language. That difference is the subject of most of this repository.

---

## Before you start

You need:

| Requirement | Why | How to check |
|-------------|-----|--------------|
| Linux or macOS | the exercise is written for a POSIX shell | `uname` |
| Python 3.12 or newer | Ansible is a Python program, and the pinned version does not install on older ones | `python3 --version` |
| Git | to get the code | `git --version` |
| Docker (optional) | one exercise runs a throwaway container; everything else works without it | `docker info` |

You do **not** need a network device, a licence, or any cloud account.

---

## Step 1 — get the code

```bash
git clone git@github.com:OfWolfAndMan/Automate-teh-Network.git
cd Automate-teh-Network
```

If SSH is not set up on your machine, use HTTPS instead:
`git clone https://github.com/OfWolfAndMan/Automate-teh-Network.git`.

What you are looking at, in the order that matters:

```text
README.md            the front door
docs/                this tutorial and its companions
playbooks/           the instructions
inventories/lab/     the machines those instructions apply to
roles/               reusable bundles of tasks
```

---

## Step 2 — install the tools

```bash
make setup
```

That runs two commands on your behalf:

```bash
python3 -m pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml -p ./collections
```

The first installs Ansible itself, at the exact version in `requirements.txt`. The second
installs **collections** — bundles of modules for particular vendors. Ansible's core does
not know how to configure a Cisco switch; `cisco.ios` does.

Expected output ends with the collection names and `was installed successfully`.

Check it worked:

```bash
ansible --version
```

You should see `core 2.21.6`.

> **If this step fails**, the error will name a package. Almost always it is one of two
> things: your Python is older than 3.11, or you are behind a proxy that blocks PyPI.
> `docs/troubleshooting.md` covers both.

---

## Step 3 — read the inventory

Ansible needs to know which machines exist. Open `inventories/lab/hosts.yml`. The part that
matters, with the rest removed:

```yaml
all:
  children:
    network:
      children:
        routers:
          hosts:
            r1:
              ansible_host: 10.0.10.11
```

Read it outwards-in:

- `all` is every machine.
- `network` is a **group** — a label you invent. Groups are how you say "run this against
  the routers".
- `routers` is a group inside `network`.
- `r1` is one machine, and `ansible_host` is where to reach it.

Further down, the same hosts appear again in groups named `cisco_ios`, `cisco_nxos` and
`arista_eos`, each carrying `ansible_network_os`. That single setting tells Ansible which
dialect to speak:

```yaml
    cisco_ios:
      hosts: [r1, r2, sw1, sw2]
      vars:
        ansible_network_os: cisco.ios.ios
        ansible_connection: network_cli
```

`network_cli` means "log in over SSH and speak the device's command line", as opposed to
`ssh`, which means "log in and run Linux commands".

Confirm Ansible can read the file:

```bash
make inventory
```

You will see a tree of groups and hosts. Nothing has connected to anything yet; this is
Ansible reading a list.

---

## Step 4 — passwords, and why the next step refuses to run

The inventory refers to `vault_ansible_password` but never defines it. That is deliberate:
a password in a file that goes into git is the single most common way automation leaks
credentials.

Instead, the value lives in a separate file that you encrypt. Copy the template, put in
throwaway local values, and encrypt it:

```bash
cp inventories/lab/group_vars/all/vault.yml.example inventories/lab/group_vars/all/vault.yml
```

Edit that file — any values will do for the exercise, because nothing real will be contacted:

```yaml
vault_ansible_password: "exercise-only"
vault_ansible_become_password: "exercise-only"
```

Now encrypt it. Ansible will ask for a password of your choosing; you will type it again
whenever you run a playbook that needs the vault:

```bash
ansible-vault encrypt inventories/lab/group_vars/all/vault.yml
```

The file on disk is now unreadable text beginning `$ANSIBLE_VAULT;1.1;AES256`. Your plaintext
values exist only while a playbook runs.

Only the *encrypted* file is ever committed; `.gitignore` already excludes the plaintext name.

---

## Step 5 — your first playbook

```bash
ansible-playbook -i inventories/lab/hosts.yml playbooks/preflight.yml --ask-vault-pass
```

Before you press enter, know what is about to happen. `preflight.yml` is a **checking**
playbook: it contacts nothing and changes nothing. It asserts three things about your setup:

1. every host in the inventory declares a network platform
2. every address falls inside the ranges this repository allows
3. the vault is populated and is not still the template

You should see, for each of seven hosts:

```text
r1                         : ok=5    changed=0    unreachable=0    failed=0
```

`ok=5` means five tasks ran, `changed=0` means none of them altered anything, `failed=0`
means none of the assertions failed. A preflight that changes something would be a bug.

> **Try breaking it on purpose.** Open `inventories/lab/hosts.yml`, change `r1`'s
> `ansible_host` to `192.168.99.99`, and run the command again. It fails, naming the host and
> the address, and telling you which ranges are allowed. Put it back afterwards. This is what
> a failing assertion is *for*: a message you can act on, before anything is touched.

---

## Step 6 — watch a machine actually converge

The network playbooks need network devices. This exercise does not: it uses a throwaway
Linux container so you can see the same mechanics on a machine you own.

Requires Docker. If you do not have it, skip to Step 7 — the concepts are identical.

```bash
make e2e-linux
```

Under the hood this starts a container, then runs `playbooks/linux/baseline.yml` against it
**twice**. The playbook installs three packages, sets the timezone, creates a user called
`ops`, and writes `/etc/motd`.

Expected, at the end:

```text
web1 : ok=5 changed=4 failed=0        <- first run: four things needed changing
web1 : ok=5 changed=0 failed=0        <- second run: everything already matched
PASS: converged on pass 1 (changed=4), changed=0 on pass 2
```

Read that pair of lines again, because it is the whole argument for this style of
automation. The first run found four differences and fixed them. The second run found none,
so it did nothing — and *the fact that it did nothing is the proof the machine matches the
description.*

> **Now break it, deliberately.**
>
> ```bash
> # 1. start a container of your own and converge it once
> docker run -d --name lab-web1 python:3.12-slim sleep infinity
> ANSIBLE_COLLECTIONS_PATH=$PWD/collections \
>   ansible-playbook -i inventories/lab/hosts.yml playbooks/linux/baseline.yml --limit web1
> # expect: ok=5  changed=4
>
> # 2. undo one thing by hand
> docker exec lab-web1 rm -f /etc/motd
>
> # 3. converge again
> ANSIBLE_COLLECTIONS_PATH=$PWD/collections \
>   ansible-playbook -i inventories/lab/hosts.yml playbooks/linux/baseline.yml --limit web1
> # expect: ok=5  changed=1   <- only the banner task acted
>
> docker rm -f lab-web1
> ```
>
> Both numbers were measured on this repository; if you see `changed=0` on step 1, the
> container was not fresh. If you see `changed=4` on step 3, you skipped step 2.
>
> A note on `ok=5` for four tasks: Ansible also counts the facts-gathering step, which is
> implicit in `gather_facts: true`.

---

### If you have no Docker

You can still do a hands-on exercise: write a five-line playbook that manages a file on your
own machine. Create `practice.yml` in the repository root:

```yaml
---
- name: Practice on this machine
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Write a file
      ansible.builtin.copy:
        content: "hello from ansible\n"
        dest: /tmp/ansible-practice.txt
        mode: "0644"
```

Run it twice:

```bash
ansible-playbook practice.yml
ansible-playbook practice.yml
```

First run: `changed=1`. Second run: `changed=0`. Delete the file by hand and run again: back
to `changed=1`. That is idempotence, demonstrated on your own machine in two minutes, with no
containers and no devices. Delete `practice.yml` afterwards; it is not part of the repository.

## Step 7 — the network playbooks, without a network

You cannot run most of these against hardware you do not have. What you *can* do is read
them, ask Ansible what they would do, and — for two of them — run them for real against
device output that is saved in the repository.

**List the tasks in a playbook without running them:**

```bash
ansible-playbook -i inventories/lab/hosts.yml playbooks/network/backup.yml --list-tasks
```

**Check that every module it names exists in the installed collections:**

```bash
ansible-doc cisco.ios.ios_config | head -30
```

That prints the manual page for the module, including every option. This is how you answer
"can Ansible do X on this device?" without guessing.

**Check it would even parse, for all hosts, without connecting:**

```bash
ansible-playbook -i inventories/lab/hosts.yml playbooks/network/backup.yml --syntax-check
```

**See what the backup role would write.** `roles/network_backup/tasks/ios.yml` asks the device
for its running configuration and saves it under `.artifacts/configs/` on *your* machine,
not the device. Read the file — it is nine lines — and notice there is no `changed_when` and
no clever logic: the module reports whether the configuration differed.

### Run one for real: compliance, offline

`playbooks/network/compliance.yml` answers a different question from the others. They
*change* devices; this one only checks them: **is each device configured the way policy says
it must be?** The saved device configurations in `tests/fixtures/backups/` are real enough to
check, so you can run it with no hardware and no vault:

```bash
ansible-playbook -i tests/compliance/hosts.yml playbooks/network/compliance.yml
```

It takes about ten seconds and ends in red, on purpose. Thirteen of the seventeen hosts pass.
Four — `SW1` to `SW4` — fail with:

```text
fatal: [SW1]: FAILED! => ... SW1: 1 of 6 policies violated — no-domain-lookup
```

That is the playbook working. Those four switches never say `no ip domain lookup`, so a
mistyped command on them would be sent to DNS as a hostname. Open
`.artifacts/compliance/report.md` for the same finding as a table, and
`policies/compliance.yml` for the rule that caught it — it is a few lines of YAML, not code.

**Now make it fail on purpose.** Copy the policies, change one rule, and point the playbook
at your copy so the repository's own file stays untouched:

```bash
cp policies/compliance.yml /tmp/strict.yml
sed -i 's/config: "ip ssh version 2"/config: "ip ssh version 1"/' /tmp/strict.yml
ansible-playbook -i tests/compliance/hosts.yml playbooks/network/compliance.yml \
  -e network_compliance_policy_file=/tmp/strict.yml
```

Now fourteen hosts fail: every router and switch that runs IOS, because none of them says
`ip ssh version 1`. The three Arista hosts still pass, because that policy does not apply to
them. Open the report again and find the new violation. Everything about how a policy is
written is in `docs/compliance.md`.

`playbooks/network/show.yml` can also run offline. It runs a `show` command, turns the text
into structured data, and can save it as JSON. Give it a capture instead of a device:

```bash
ansible-playbook -i tests/show/hosts.yml playbooks/network/show.yml \
  -e 'show_text_file=tests/fixtures/show/{{ inventory_hostname }}_show_version.txt'
```

Look for the `serial` list in the output: a switch *stack* has one serial per member, which is
why it prints as a list.

Both are marked `partial` in the README table. What ran here is the parsing, the checking and
the report. What did not run is the step that collects the text from a live device.

### Pointing it at a real device

When you have one — a lab switch, Cisco CML, Arista cEOS, GNS3 with an IOS image — you need
three things in the inventory: where it is, which dialect it speaks, and how to log in.

The smallest complete `inventories/lab/hosts.yml` that works for one device:

```yaml
---
all:
  children:
    network:
      children:
        cisco_ios:
          hosts:
            myswitch:
              ansible_host: 192.0.2.10
          vars:
            ansible_network_os: cisco.ios.ios
            ansible_connection: network_cli
            ansible_user: admin
            ansible_password: "{{ vault_ansible_password }}"
```

Notice the shape: `network` is a group, `cisco_ios` is a group inside it, and `myswitch` is a
host inside that. The `vars:` block belongs to the `cisco_ios` group, so every device in it
gets the same dialect and credentials. The password is a reference to the vault, never a
literal.

Then:

```bash
ansible-playbook -i inventories/lab/hosts.yml playbooks/network/backup.yml --ask-vault-pass
```

The configuration lands in `.artifacts/configs/myswitch.cfg` on your machine. Open it. If it
matches what `show running-config` gives you on the device, the whole chain worked.

If it fails, the failure will name the host and the port. `docs/troubleshooting.md` lists the
four errors that account for almost all first attempts.

---

## Step 8 — where to go next

- `docs/glossary.md` — every term in this repository, in one sentence each.
- `docs/reading-a-playbook.md` — one playbook annotated line by line.
- `docs/compliance.md` — write your own policy and check a device against it.
- `examples/python/README.md` — seven short Python programs for when Ansible is not the right
  tool: regular expressions, parsing, SQL, classes, asyncio, logging. Four run offline.
- `docs/architecture.md` — why the repository is arranged this way.
- `docs/addressing-and-placeholder-standard.md` — the rule that keeps credentials and real
  addresses out of the repository.
- `CONTRIBUTING.md` — the two rules a change has to satisfy.

---

## Cheat sheet

```bash
make setup            # install the pinned toolchain (once)
make inventory        # show the machines Ansible knows about
make preflight        # check the setup; contacts nothing
make test             # scrub, inventory, syntax, README index, docs, pytest,
                      # and the compliance and show playbooks run offline
make full             # everything above, plus the container exercise

ansible-playbook -i inventories/lab/hosts.yml <playbook> --ask-vault-pass
ansible-playbook -i inventories/lab/hosts.yml <playbook> --list-tasks
ansible-playbook -i inventories/lab/hosts.yml <playbook> --syntax-check
ansible-doc <collection.module>            # the manual page for one module
ansible-vault edit <file>                  # change an encrypted file
```

Three habits worth adopting now:

1. **Run `--syntax-check` before anything else.** It costs a second and catches typos that
   would otherwise fail halfway through a change.
2. **Read `changed=` on every run.** `changed=0` on a second run is the signal that your
   description was complete. `changed=1` every time is a description that does not hold.
3. **Never put a real credential in a file that git can see.** The vault step exists because
   the alternative is a leaked password in a public repository.
