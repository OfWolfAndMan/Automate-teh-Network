"""The compliance engine, against synthetic configs and the real backup fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

import compliance as c

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "backups"
POLICIES = yaml.safe_load((ROOT / "policies/compliance.yml").read_text())["compliance_policies"]
SCHEMA = json.loads((ROOT / "policies/compliance.schema.json").read_text())


def policy(**kw):
    base = {"id": "p", "description": "d", "platforms": ["ios"], "config": "x"}
    return {**base, **kw}


def one(text: str, **kw) -> dict:
    [result] = c.check(text, [policy(**kw)], "ios")
    return result


# --- parser ---------------------------------------------------------------------------

def test_parse_builds_parent_child_tree_and_drops_comments():
    tree = c.parse("hostname r1\n!\nline vty 0 4\n transport input ssh\n  nested\nend\n")
    assert [n.text for n in tree] == ["hostname r1", "line vty 0 4", "end"]
    assert [n.text for n in tree[1].children] == ["transport input ssh"]
    assert [n.text for n in tree[1].children[0].children] == ["nested"]


def test_parse_collapses_whitespace_so_eos_three_space_indent_parses():
    tree = c.parse("interface  Ethernet1\n   description   uplink\n")
    assert tree[0].text == "interface Ethernet1"
    assert tree[0].children[0].text == "description uplink"


def test_banner_body_is_not_read_as_configuration():
    cfg = "banner login ^CC\nno ip http server\nwarning text\n^C\nip ssh version 2\n"
    assert [n.text for n in c.parse(cfg)] == ["ip ssh version 2"]


def test_single_line_banner_does_not_swallow_the_rest():
    cfg = "banner motd ^Chello^C\nip ssh version 2\n"
    assert [n.text for n in c.parse(cfg)] == ["ip ssh version 2"]


# --- semantics ------------------------------------------------------------------------

def test_match_is_whole_line_not_substring():
    assert not one("ip ssh version 2 extra\n", config="ip ssh version 2")["compliant"]
    assert one("ip ssh version 2\n", config="ip ssh version 2")["compliant"]


def test_top_level_policy_ignores_indented_lines():
    assert not one("interface Gi1\n no ip http server\n", config="no ip http server")["compliant"]


def test_present_under_parent_requires_every_matching_block():
    cfg = "line vty 0 4\n transport input ssh\nline vty 5 15\n transport input telnet\n"
    r = one(cfg, parent="line vty .*", config="transport input (ssh|none)")
    assert not r["compliant"]
    assert r["detail"] == "missing under: line vty 5 15"


def test_present_under_parent_fails_when_no_block_exists():
    r = one("hostname r1\n", parent="line vty .*", config="transport input ssh")
    assert not r["compliant"]
    assert "no block matches" in r["detail"]


def test_absent_top_level_and_under_parent():
    cfg = "snmp-server community public RO\nline vty 0 4\n transport input telnet\n"
    snmp = one(cfg, config="snmp-server community[ ](public|private)( .*)?", state="absent")
    assert not snmp["compliant"] and "public RO" in snmp["detail"]
    vty = one(cfg, parent="line vty .*", config="transport input .*telnet.*", state="absent")
    assert not vty["compliant"] and "line vty 0 4 -> transport input telnet" in vty["detail"]
    assert one("hostname r1\n", config="snmp-server community[ ].*", state="absent")["compliant"]


def test_platform_and_group_scoping():
    pols = [policy(id="ios-all"), policy(id="ios-sw", groups=["switches"]),
            policy(id="eos", platforms=["eos"])]
    ids = lambda plat, groups: [r["id"] for r in c.check("x\n", pols, plat, groups)]  # noqa: E731
    assert ids("ios", ["routers"]) == ["ios-all"]
    assert ids("cisco.ios.ios", ["switches", "network"]) == ["ios-all", "ios-sw"]
    assert ids("arista.eos.eos", []) == ["eos"]


def test_unknown_platform_and_bad_regex_are_errors_not_passes():
    with pytest.raises(ValueError, match="platform"):
        c.check("x\n", [policy()], "junos")
    with pytest.raises(ValueError, match="not a valid regex"):
        c.check("x\n", [policy(config="(")], "ios")


def test_filter_raises_ansible_error():
    from ansible.errors import AnsibleFilterError

    with pytest.raises(AnsibleFilterError):
        c.FilterModule().filters()["compliance_check"]("x\n", [policy(config="(")], "ios")


# --- the shipped policy file -----------------------------------------------------------

def test_shipped_policies_satisfy_the_schema():
    jsonschema.validate(POLICIES, SCHEMA)


def test_schema_rejects_the_course_era_shape():
    # The mini-course keyed on `platform` (singular), `device_types` and a "None" string.
    course = [{"name": "SSH Version 2", "description": "d", "platform": "IOS",
               "device_types": ["router"], "config": "ip ssh version 2", "parent": "None"}]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(course, SCHEMA)


def test_policy_ids_are_unique():
    ids = [p["id"] for p in POLICIES]
    assert len(ids) == len(set(ids))


# --- the shipped policies against the real fixtures ------------------------------------
# Expected results were read off the fixtures by hand (grep), not copied from the engine.

def fixture_host(name: str) -> tuple[str, str, list[str]]:
    text = (FIXTURES / name / f"{name}.cfg").read_text()
    if name.startswith("vEOS"):
        return text, "eos", ["fabric"]
    return text, "ios", ["switches"] if name.startswith("SW") else ["routers"]


def violations(name: str) -> list[str]:
    text, platform, groups = fixture_host(name)
    return [r["id"] for r in c.check(text, POLICIES, platform, groups) if not r["compliant"]]


@pytest.mark.parametrize("name", [f"IOSV{i}" for i in range(1, 11)])
def test_lab_routers_are_compliant(name):
    assert violations(name) == []


@pytest.mark.parametrize("name", ["SW1", "SW2", "SW3", "SW4"])
def test_switches_still_resolve_typos_as_hostnames(name):
    # The switches carry `ip domain-name` but never `no ip domain lookup`.
    assert violations(name) == ["no-domain-lookup"]


@pytest.mark.parametrize("name", ["vEOS1", "vEOS2", "vEOS3"])
def test_eos_fabric_is_compliant(name):
    assert violations(name) == []


def test_switch_policy_count_includes_the_group_scoped_policy():
    text, platform, groups = fixture_host("SW1")
    assert len(c.check(text, POLICIES, platform, groups)) == 6
    text, platform, _ = fixture_host("IOSV1")
    assert len(c.check(text, POLICIES, platform, ["routers"])) == 5
