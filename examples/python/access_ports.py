"""Regular expressions: pull access ports out of a switch configuration.

Lesson: a regex with *named groups* says what each piece means, and `re.VERBOSE` lets the
pattern carry comments. Matching one interface block at a time — rather than one giant
pattern across the whole file — keeps the regex small enough to read.

Modernised from the mini-course's shared/regex-prototype.py, which opened a file that
was never committed, assumed description and access VLAN sat on fixed neighbouring lines,
and broke as soon as another command came between them.

Runs offline against the repository's fixtures:

    python examples/python/access_ports.py tests/fixtures/backups/SW1/SW1.cfg
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

# One interface block: the header line, then every indented line under it.
BLOCK = re.compile(r"^interface (?P<name>\S+)\n(?P<body>(?:[ \t].*\n?)*)", re.MULTILINE)

ACCESS_VLAN = re.compile(r"""
    ^\s*switchport\ access\ vlan\ (?P<vlan>\d{1,4})\s*$   # the VLAN, 1-4 digits
""", re.MULTILINE | re.VERBOSE)

DESCRIPTION = re.compile(r"^\s*description (?P<text>.+?)\s*$", re.MULTILINE)
SHUTDOWN = re.compile(r"^\s*shutdown\s*$", re.MULTILINE)


@dataclass(frozen=True)
class AccessPort:
    name: str
    vlan: int
    description: str
    shutdown: bool


def access_ports(config: str) -> list[AccessPort]:
    ports = []
    for block in BLOCK.finditer(config):
        body = block["body"]
        vlan = ACCESS_VLAN.search(body)
        if not vlan:
            continue  # a trunk, a routed port, or an access port left in VLAN 1
        desc = DESCRIPTION.search(body)
        ports.append(AccessPort(
            name=block["name"],
            vlan=int(vlan["vlan"]),
            description=desc["text"] if desc else "",
            shutdown=bool(SHUTDOWN.search(body)),
        ))
    return ports


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("config", type=Path)
    a = ap.parse_args()
    for p in access_ports(a.config.read_text()):
        state = "shutdown" if p.shutdown else "up"
        print(f"{p.name:<24} vlan {p.vlan:<5} {state:<9} {p.description}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
