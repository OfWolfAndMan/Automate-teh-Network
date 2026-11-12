# Python examples

Five short programs, each teaching one idea a network engineer reaches for once Ansible is
not enough. They are the modernised teaching scripts from the 2019–2021
*Network-Automation-Mini-Course*. What changed, and what was retired instead, is recorded in
[`docs/retirements.md`](../../docs/retirements.md).

| File | The idea | Needs a device? |
|------|----------|-----------------|
| [`access_ports.py`](access_ports.py) | regular expressions with named groups, one config block at a time | no — reads `tests/fixtures/backups/` |
| [`show_version_csv.py`](show_version_csv.py) | parse show commands with ntc-templates, write CSV | no — reads `tests/fixtures/show/` |
| [`inventory_db.py`](inventory_db.py) | SQL: load the Ansible inventory into SQLite; placeholders, not f-strings | no — reads `inventories/lab/` |
| [`device.py`](device.py) | classes, inheritance and a context manager around one Netmiko connection | yes |
| [`concurrent_show.py`](concurrent_show.py) | asyncio for blocking libraries: `to_thread`, `gather`, a semaphore | yes |

## Run them

From the repository root, after `make setup`:

```bash
python examples/python/access_ports.py tests/fixtures/backups/SW1/SW1.cfg
python examples/python/show_version_csv.py tests/fixtures/show/*_show_version.txt
python examples/python/inventory_db.py --group switches
```

The two that log in read credentials from the environment, never from the file:

```bash
export LAB_USERNAME=lab
read -rs LAB_PASSWORD && export LAB_PASSWORD     # typed, not left in shell history
python examples/python/device.py 10.0.10.11 "show version"
python examples/python/concurrent_show.py "show clock" 10.0.10.11 10.0.10.12 --limit 5
```

## Four habits every file follows

- **Nothing runs on import.** Each file has a `main()` called only under
  `if __name__ == "__main__":`. Several course scripts logged in to a device the moment
  another file imported them.
- **No credential in source.** Credentials come from the environment, and `repr()` of a
  device never prints its password.
- **Testable without a network.** `examples/python/tests/` runs every example offline. The
  parsers read the fixtures, and anything that would open an SSH session gets a fake.
- **Pinned dependencies.** [`requirements.txt`](requirements.txt) pins Netmiko and
  ntc-templates. The Ansible toolchain does not need either.

```bash
make pytest     # includes these tests
```
