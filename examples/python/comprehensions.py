"""Comprehensions: reshape the lab inventory in one readable line at a time.

Lesson: a list, dict or set comprehension builds a new collection from an old one —
`[x for x in things if test(x)]` — without the append-in-a-loop boilerplate. And when the
test is about IP addresses, use the `ipaddress` module rather than string prefixes.

Modernised from NotLayer3's advanced_python/comprehensions.py, which filtered addresses
with `entry.startswith("192.168.")` — a test that also accepts "192.168.1.300", and whose
cousin `startswith("10.1")` quietly matches 10.10.x and 10.100.x too — and built a dict
comprehension that copied all of an entry's fields or none of them.

Runs offline against the repository's own inventory:

    python examples/python/comprehensions.py
"""

from __future__ import annotations

import ipaddress

from inventory_db import inventory_json

# The repository's declared address planes (docs/addressing-and-placeholder-standard.md).
PLANES = {
    "internal": ipaddress.ip_network("10.0.0.0/16"),
    "external": ipaddress.ip_network("198.18.0.0/15"),
    "example": ipaddress.ip_network("192.0.2.0/24"),
    "example-2": ipaddress.ip_network("198.51.100.0/24"),
    "example-3": ipaddress.ip_network("203.0.113.0/24"),
}


def plane_of(address: str) -> str | None:
    """The plane an address belongs to, or None. Invalid text is None, not an exception."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return None
    # A generator inside next(): stop at the first plane that contains the address.
    return next((name for name, net in PLANES.items() if ip in net), None)


def network_hosts(hostvars: dict[str, dict]) -> dict[str, dict]:
    """Dict comprehension: keep only hosts that declare a network platform."""
    return {host: hv for host, hv in hostvars.items() if hv.get("ansible_network_os")}


def platforms(hosts: dict[str, dict]) -> set[str]:
    """Set comprehension: each platform once, however many hosts run it."""
    return {hv["ansible_network_os"].rsplit(".", 1)[-1] for hv in hosts.values()}


def by_platform(hosts: dict[str, dict]) -> dict[str, list[str]]:
    """A dict comprehension whose values are list comprehensions."""
    return {
        p: sorted(h for h, hv in hosts.items() if hv["ansible_network_os"].endswith(f".{p}"))
        for p in sorted(platforms(hosts))
    }


def outside_planes(hosts: dict[str, dict]) -> list[str]:
    """List comprehension: the hosts whose address is in no declared plane."""
    return sorted(h for h, hv in hosts.items() if plane_of(hv.get("ansible_host", "")) is None)


def main() -> int:
    hosts = network_hosts(inventory_json()["_meta"]["hostvars"])
    for platform, names in by_platform(hosts).items():
        print(f"{platform:<5} {', '.join(names)}")
    stray = outside_planes(hosts)
    print(f"{len(hosts)} network hosts; outside every declared plane: {', '.join(stray) or 'none'}")
    return 1 if stray else 0


if __name__ == "__main__":
    raise SystemExit(main())
