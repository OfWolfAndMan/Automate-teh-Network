"""Classes for network devices: a wrapper around one Netmiko connection.

Lesson: a class bundles the data a device needs (address, credentials, platform) with the
things you do to it (connect, run a command, disconnect), and a context manager makes the
disconnect impossible to forget.

Modernised from the mini-course's Classes/objects.py, which connected to a device with a
hard-coded password the moment the file was imported, and assumed a connection existed
before checking (`if self.connection:` raised AttributeError when it did not).

    export LAB_USERNAME=lab LAB_PASSWORD=...        # never in the file
    python examples/python/device.py 192.0.2.11 "show version" --device-type cisco_ios
"""

from __future__ import annotations

import argparse
import os
from typing import Any


class CredentialsMissing(RuntimeError):
    pass


def credentials_from_env() -> tuple[str, str]:
    """Credentials come from the environment, never from source code."""
    user, password = os.environ.get("LAB_USERNAME"), os.environ.get("LAB_PASSWORD")
    if not user or not password:
        raise CredentialsMissing("set LAB_USERNAME and LAB_PASSWORD in the environment")
    return user, password


class NetworkDevice:
    def __init__(self, host: str, username: str, password: str,
                 device_type: str = "cisco_ios", port: int = 22) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type
        self.port = port
        self._conn: Any = None

    def __repr__(self) -> str:
        # Written by hand so the password is never printed, not even in a traceback.
        return (f"{type(self).__name__}(host={self.host!r}, username={self.username!r}, "
                f"device_type={self.device_type!r})")

    @classmethod
    def from_env(cls, host: str, device_type: str = "cisco_ios") -> NetworkDevice:
        user, password = credentials_from_env()
        return cls(host, user, password, device_type)

    @property
    def connected(self) -> bool:
        return self._conn is not None

    def connect(self) -> NetworkDevice:
        # Imported here so the rest of the class (and its tests) work without Netmiko.
        from netmiko import ConnectHandler

        self._conn = ConnectHandler(
            device_type=self.device_type, host=self.host, port=self.port,
            username=self.username, password=self.password,
        )
        return self

    def send(self, command: str) -> str:
        if not self.connected:
            raise RuntimeError(f"{self.host}: not connected — call connect() or use `with`")
        return self._conn.send_command(command)

    def disconnect(self) -> None:
        if self.connected:
            self._conn.disconnect()
            self._conn = None

    # The context manager: `with NetworkDevice(...) as dev:` connects on entry and
    # disconnects on exit — including when the body raises.
    def __enter__(self) -> NetworkDevice:
        return self.connect()

    def __exit__(self, *exc: object) -> None:
        self.disconnect()


class Router(NetworkDevice):
    """Inheritance: a Router is a NetworkDevice that can also report its prompt."""

    def prompt(self) -> str:
        if not self.connected:
            raise RuntimeError(f"{self.host}: not connected")
        return self._conn.find_prompt()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("host")
    ap.add_argument("command")
    ap.add_argument("--device-type", default="cisco_ios")
    a = ap.parse_args()
    with NetworkDevice.from_env(a.host, a.device_type) as dev:
        print(dev.send(a.command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
