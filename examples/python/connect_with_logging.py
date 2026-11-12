"""Logging and exceptions: connect to many devices, and say exactly why each one failed.

Lesson: a bare `except:` turns every failure — a wrong password, a dead host, a typo in
your own code — into the same "connection error". Catch the specific exceptions you can
explain, let the rest crash loudly, and log through the `logging` module so the output can
go to a file, the terminal, or both without touching the code that produces it.

Modernised from NotLayer3's basic-python/connections.py and utils.get_config(), which
configured logging at import time (so importing utils created log.txt in whatever directory
you happened to be in), kept passwords in the source, caught everything with a bare
`except:`, and wrote 24,000 lines of log into the repository.

    export LAB_USERNAME=lab LAB_PASSWORD=...
    python examples/python/connect_with_logging.py 192.0.2.11 192.0.2.12 --log connect.log
"""

from __future__ import annotations

import argparse
import logging
import socket
from collections.abc import Callable
from dataclasses import dataclass

from device import NetworkDevice, credentials_from_env

# A module gets a named logger and never configures it: configuration is main()'s job, so
# importing this file has no side effects.
log = logging.getLogger("connect")


@dataclass
class Outcome:
    host: str
    ok: bool
    reason: str = ""


def _known_failures() -> tuple[tuple[type[BaseException], str], ...]:
    """The failures we can explain, most specific first."""
    from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

    return (
        (NetmikoAuthenticationException, "authentication failed"),
        (NetmikoTimeoutException, "timed out — host down, or SSH not listening"),
        (ConnectionRefusedError, "connection refused — nothing listening on the port"),
        (socket.gaierror, "name does not resolve"),
    )


def try_host(host: str, connect: Callable[[str], object]) -> Outcome:
    known = _known_failures()
    try:
        connect(host)
    except tuple(exc for exc, _ in known) as exc:
        reason = next(why for cls, why in known if isinstance(exc, cls))
        log.warning("%s: %s", host, reason)  # %-style: formatted only if the level is on
        return Outcome(host, False, reason)
    # Anything else is a bug or a surprise, not a device problem: let it propagate.
    log.info("%s: connected", host)
    return Outcome(host, True)


def login_and_out(host: str, device_type: str, user: str, password: str) -> None:
    with NetworkDevice(host, user, password, device_type) as dev:
        dev.send("show clock")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("hosts", nargs="+")
    ap.add_argument("--device-type", default="cisco_ios")
    ap.add_argument("--log", help="also write the log to this file")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if a.log:
        handlers.append(logging.FileHandler(a.log))
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s", handlers=handlers)

    user, password = credentials_from_env()
    outcomes = [try_host(h, lambda h: login_and_out(h, a.device_type, user, password))
                for h in a.hosts]
    failed = [o for o in outcomes if not o.ok]
    log.info("%d of %d devices reachable", len(outcomes) - len(failed), len(outcomes))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
