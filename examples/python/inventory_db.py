"""SQL for network engineers: load the Ansible inventory into SQLite and query it.

Lesson: a database answers questions an inventory file cannot answer quickly ("every IOS
device whose address is in 192.0.2.0/24"). Two rules carry most of the safety:

  1. VALUES go through placeholders (`?`), never through f-strings. The driver quotes
     them, so a hostname like `x'; DROP TABLE devices; --` is stored as a strange name
     rather than run as a command.
  2. IDENTIFIERS (table and column names) cannot be placeholders. When one must vary,
     check it against a fixed allow-list before it goes anywhere near the SQL text.

Modernised from the mini-course's get_dbentries_postgres(), which built
`SELECT * FROM {table}` with an f-string, needed a PostgreSQL server and psycopg2, and
printed instead of returning. SQLite ships with Python, so this runs anywhere.

    python examples/python/inventory_db.py --platform ios
    python examples/python/inventory_db.py --group switches --db lab.sqlite
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "inventories" / "lab" / "hosts.yml"

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    hostname TEXT PRIMARY KEY,
    platform TEXT,          -- last component of ansible_network_os: ios, nxos, eos
    address  TEXT
);
CREATE TABLE IF NOT EXISTS memberships (
    hostname TEXT REFERENCES devices(hostname) ON DELETE CASCADE,
    grp      TEXT,
    PRIMARY KEY (hostname, grp)
);
"""

# Rule 2: the only columns a caller may sort by.
SORTABLE = {"hostname", "platform", "address"}


def inventory_json(inventory: Path = INVENTORY) -> dict:
    """The inventory as Ansible itself resolves it — group_vars, children and all."""
    exe = shutil.which("ansible-inventory")
    if exe is None:
        raise RuntimeError("ansible-inventory not found; run `make setup` first")
    out = subprocess.run([exe, "-i", str(inventory), "--list"],  # noqa: S603 — fixed argv
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def rows_from_inventory(inv: dict) -> tuple[list[tuple], list[tuple]]:
    hostvars = inv.get("_meta", {}).get("hostvars", {})
    devices = []
    for host, hv in sorted(hostvars.items()):
        nos = hv.get("ansible_network_os")
        if not nos:
            continue  # not a network device (e.g. the linux lab container)
        devices.append((host, nos.rsplit(".", 1)[-1], hv.get("ansible_host")))
    names = {d[0] for d in devices}
    members = sorted({(h, grp) for grp, body in inv.items() if grp not in ("_meta", "all")
                      for h in body.get("hosts", []) if h in names})
    return devices, members


def load(conn: sqlite3.Connection, inv: dict) -> int:
    conn.executescript(SCHEMA)
    devices, members = rows_from_inventory(inv)
    with conn:  # one transaction: all of it lands, or none of it does
        conn.executemany("INSERT OR REPLACE INTO devices VALUES (?, ?, ?)", devices)
        conn.executemany("INSERT OR IGNORE INTO memberships VALUES (?, ?)", members)
    return len(devices)


def find(conn: sqlite3.Connection, platform: str | None = None, group: str | None = None,
         order_by: str = "hostname") -> list[tuple]:
    if order_by not in SORTABLE:  # rule 2
        raise ValueError(f"cannot sort by {order_by!r}; choose from {sorted(SORTABLE)}")
    sql = "SELECT DISTINCT d.hostname, d.platform, d.address FROM devices d"
    params: list[str] = []
    if group:
        sql += " JOIN memberships m ON m.hostname = d.hostname AND m.grp = ?"
        params.append(group)
    if platform:
        sql += " WHERE d.platform = ?"
        params.append(platform)
    sql += f" ORDER BY d.{order_by}"  # noqa: S608 — allow-listed identifier, not a value
    return conn.execute(sql, params).fetchall()  # rule 1: values only via `params`


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--platform", help="ios, nxos or eos")
    ap.add_argument("--group", help="an inventory group, e.g. switches")
    ap.add_argument("--order-by", default="hostname", choices=sorted(SORTABLE))
    ap.add_argument("--db", default=":memory:", help="SQLite file (default: in memory)")
    a = ap.parse_args()

    conn = sqlite3.connect(a.db)
    n = load(conn, inventory_json())
    rows = find(conn, a.platform, a.group, a.order_by)
    for host, platform, address in rows:
        print(f"{host:<8} {platform:<5} {address}")
    print(f"{len(rows)} of {n} network devices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
