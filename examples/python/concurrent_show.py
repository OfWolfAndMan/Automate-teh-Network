"""Run one command on many devices at once, with asyncio.

Lesson: Netmiko is *blocking* — it waits on SSH. Calling it from an `async def` does not
make it concurrent; the event loop just waits too. `asyncio.to_thread` hands each blocking
call to a worker thread, `asyncio.gather` waits for all of them, and a semaphore caps how
many devices are logged into at once (a vty line is a finite resource).

Modernised from the mini-course's uncategorized/netmiko_async.py, which called blocking
Netmiko inside coroutines (so ran one device at a time), used the deprecated
`asyncio.get_event_loop()`, popped a single host off its list, and ran on import.

    export LAB_USERNAME=lab LAB_PASSWORD=...
    python examples/python/concurrent_show.py "show clock" 10.0.10.11 10.0.10.12 --limit 5
"""

from __future__ import annotations

import argparse
import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass

from device import NetworkDevice, credentials_from_env


@dataclass
class Result:
    host: str
    output: str | None = None
    error: str | None = None


def show(host: str, command: str, device_type: str, user: str, password: str) -> str:
    """The blocking unit of work: one login, one command, one logout."""
    with NetworkDevice(host, user, password, device_type) as dev:
        return dev.send(command)


async def run_all(hosts: list[str], work: Callable[[str], str], limit: int = 10) -> list[Result]:
    """Run `work(host)` for every host, at most `limit` at a time, in input order.

    One device failing does not cancel the others: its error is recorded in its Result.
    """
    gate = asyncio.Semaphore(limit)

    async def one(host: str) -> Result:
        async with gate:
            try:
                return Result(host, output=await asyncio.to_thread(work, host))
            except Exception as exc:  # report every failure, per device, and carry on
                return Result(host, error=f"{type(exc).__name__}: {exc}")

    return await asyncio.gather(*(one(h) for h in hosts))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command")
    ap.add_argument("hosts", nargs="+")
    ap.add_argument("--device-type", default="cisco_ios")
    ap.add_argument("--limit", type=int, default=10, help="devices logged into at once")
    a = ap.parse_args()

    user, password = credentials_from_env()
    started = time.perf_counter()
    results = asyncio.run(run_all(
        a.hosts, lambda h: show(h, a.command, a.device_type, user, password), a.limit))
    for r in results:
        print(f"===== {r.host}")
        print(r.output if r.error is None else f"FAILED: {r.error}")
    print(f"{len(results)} devices in {time.perf_counter() - started:.1f}s")
    return 1 if any(r.error for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
