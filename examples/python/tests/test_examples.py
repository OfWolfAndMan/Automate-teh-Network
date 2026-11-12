"""The examples, tested offline: fixtures for parsing, fakes for anything that would SSH."""

from __future__ import annotations

import asyncio
import shutil
import sqlite3
import sys
import threading
import time
import types
from pathlib import Path

import pytest

import access_ports
import concurrent_show
import device
import inventory_db
import show_version_csv

ROOT = Path(__file__).resolve().parents[3]
BACKUPS = ROOT / "tests" / "fixtures" / "backups"
SHOW = ROOT / "tests" / "fixtures" / "show"


# --- device.py --------------------------------------------------------------------------

class FakeConnection:
    instances: list[FakeConnection] = []

    def __init__(self, **kwargs):
        self.kwargs, self.closed = kwargs, False
        FakeConnection.instances.append(self)

    def send_command(self, command):
        return f"output of {command}"

    def find_prompt(self):
        return "r1#"

    def disconnect(self):
        self.closed = True


@pytest.fixture
def fake_netmiko(monkeypatch):
    FakeConnection.instances.clear()
    fake = types.SimpleNamespace(ConnectHandler=FakeConnection)
    monkeypatch.setitem(sys.modules, "netmiko", fake)
    return FakeConnection


def test_context_manager_disconnects_even_when_the_body_raises(fake_netmiko):
    with pytest.raises(ZeroDivisionError), device.NetworkDevice("192.0.2.11", "u", "p") as dev:
        assert dev.send("show clock") == "output of show clock"
        1 / 0  # noqa: B018
    assert fake_netmiko.instances[0].closed
    assert not dev.connected


def test_password_never_appears_in_repr():
    assert "s3cret" not in repr(device.NetworkDevice("192.0.2.11", "u", "s3cret"))


def test_send_before_connect_is_a_clear_error_not_an_attribute_error():
    with pytest.raises(RuntimeError, match="not connected"):
        device.NetworkDevice("192.0.2.11", "u", "p").send("show clock")


def test_router_inherits_and_extends(fake_netmiko):
    with device.Router("192.0.2.11", "u", "p") as r:
        assert r.prompt() == "r1#"
        assert r.send("x") == "output of x"


def test_credentials_come_from_the_environment(monkeypatch):
    monkeypatch.delenv("LAB_USERNAME", raising=False)
    monkeypatch.delenv("LAB_PASSWORD", raising=False)
    with pytest.raises(device.CredentialsMissing):
        device.NetworkDevice.from_env("192.0.2.11")
    monkeypatch.setenv("LAB_USERNAME", "lab")
    monkeypatch.setenv("LAB_PASSWORD", "pw")
    assert device.NetworkDevice.from_env("192.0.2.11").username == "lab"


# --- concurrent_show.py -----------------------------------------------------------------

def test_semaphore_caps_concurrency_and_order_is_preserved():
    active = peak = 0
    lock = threading.Lock()

    def work(host):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.05)
        with lock:
            active -= 1
        return host.upper()

    hosts = [f"h{i}" for i in range(8)]
    results = asyncio.run(concurrent_show.run_all(hosts, work, limit=3))
    assert [r.output for r in results] == [h.upper() for h in hosts]
    assert peak == 3


def test_one_failing_device_does_not_cancel_the_rest():
    def work(host):
        if host == "bad":
            raise TimeoutError("no answer")
        return "ok"

    results = asyncio.run(concurrent_show.run_all(["a", "bad", "c"], work))
    assert [(r.output, r.error) for r in results] == [
        ("ok", None), (None, "TimeoutError: no answer"), ("ok", None)]


# --- access_ports.py --------------------------------------------------------------------

@pytest.mark.parametrize(
    ("switch", "expected"), [("SW1", 16), ("SW2", 16), ("SW3", 0), ("SW4", 41)]
)
def test_finds_every_access_port_in_the_fixtures(switch, expected):
    # expected = `grep -c 'switchport access vlan' tests/fixtures/backups/SWn/SWn.cfg`
    config = (BACKUPS / switch / f"{switch}.cfg").read_text()
    assert len(access_ports.access_ports(config)) == expected


def test_tolerates_commands_between_description_and_vlan():
    # The course's prototype required these on fixed neighbouring lines.
    cfg = ("interface Gi1/0/5\n description printer\n switchport mode access\n"
           " spanning-tree portfast\n switchport access vlan 30\n shutdown\n!\n"
           "interface Gi1/0/6\n switchport mode trunk\n")
    [port] = access_ports.access_ports(cfg)
    assert port == access_ports.AccessPort("Gi1/0/5", 30, "printer", True)


# --- show_version_csv.py ----------------------------------------------------------------

def test_parses_both_captures_and_keeps_every_stack_member(tmp_path):
    rows = [show_version_csv.parse_show_version(p.read_text())
            for p in sorted(SHOW.glob("*_show_version.txt"))]
    assert [r["hostname"] for r in rows] == ["sw1", "sw2"]
    assert all(len(r["serial"].split()) == 2 for r in rows)  # two-member stacks
    out = tmp_path / "inv.csv"
    with out.open("w", newline="") as fh:
        show_version_csv.write_csv(rows, fh)
    assert out.read_text().splitlines()[0] == ",".join(show_version_csv.FIELDS)


# --- inventory_db.py --------------------------------------------------------------------

INV = {
    "_meta": {"hostvars": {
        "r1": {"ansible_network_os": "cisco.ios.ios", "ansible_host": "192.0.2.11"},
        "sw1": {"ansible_network_os": "cisco.ios.ios", "ansible_host": "192.0.2.21"},
        "eos1": {"ansible_network_os": "arista.eos.eos", "ansible_host": "192.0.2.41"},
        "web1": {"ansible_connection": "community.docker.docker"},
    }},
    "routers": {"hosts": ["r1"]},
    "switches": {"hosts": ["sw1"]},
    "linux": {"hosts": ["web1"]},
}


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    inventory_db.load(conn, INV)
    yield conn
    conn.close()


def test_loads_network_devices_only(db):
    assert [r[0] for r in inventory_db.find(db)] == ["eos1", "r1", "sw1"]


def test_filters_by_platform_and_group(db):
    rows = inventory_db.find(db, platform="ios", group="switches")
    assert rows == [("sw1", "ios", "192.0.2.21")]


def test_a_hostile_value_is_data_not_sql(db):
    assert inventory_db.find(db, platform="ios' OR '1'='1") == []
    assert inventory_db.find(db, group="x'; DROP TABLE devices; --") == []
    assert len(inventory_db.find(db)) == 3  # the table is still there


def test_identifiers_are_allow_listed(db):
    with pytest.raises(ValueError, match="cannot sort by"):
        inventory_db.find(db, order_by="hostname; DROP TABLE devices")


@pytest.mark.skipif(shutil.which("ansible-inventory") is None, reason="needs ansible-core")
def test_against_the_real_lab_inventory():
    conn = sqlite3.connect(":memory:")
    assert inventory_db.load(conn, inventory_db.inventory_json()) == 7
    assert [r[0] for r in inventory_db.find(conn, group="switches")] == ["sw1", "sw2"]
