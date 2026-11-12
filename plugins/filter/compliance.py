"""Configuration compliance: does a running configuration satisfy a set of policies?

Successor to the compliance checker in the 2019-2021 Network-Automation-Mini-Course, which
asked the same question through a Flask API, a CiscoConfParse v1 dependency and a pipeline
that could not start (its provisioning modules were never committed). The question was the
right one; this is the smallest thing that answers it.

A policy is data:

    - id: ssh-only-vty
      description: VTY lines accept SSH or nothing
      platforms: [ios]          # the last component of ansible_network_os
      groups: [routers]         # optional; inventory groups the policy applies to
      parent: "line vty .*"     # optional; selects top-level blocks
      config: "transport input (ssh|none)"
      state: present            # present (default) | absent

Every pattern is a regular expression matched against the WHOLE line (re.fullmatch), after
indentation is stripped and runs of whitespace are collapsed. "ip ssh version 2" therefore
matches that line and not "ip ssh version 2 foo".

Semantics:

  no parent, present   some top-level line matches `config`
  no parent, absent    no top-level line matches `config`
  parent, present      at least one block matches `parent`, and EVERY such block has a
                       direct child matching `config` (a policy about "the vty lines" is
                       about all of them)
  parent, absent       no block matching `parent` has a direct child matching `config`

The parser is indentation-based and stdlib-only. ciscoconfparse2 was evaluated and not
adopted: thirteen runtime dependencies (hypothesis among them) and no EOS syntax mode,
for a job that is one tree walk.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

PLATFORMS = ("ios", "nxos", "eos")

_WS = re.compile(r"\s+")
_BANNER = re.compile(r"^banner\s+\S+\s+(\^C|\S)")


@dataclass
class Line:
    text: str
    children: list[Line] = field(default_factory=list)


def parse(config: str) -> list[Line]:
    """Parse an indented configuration into top-level lines with their children.

    Comment lines (`!`), blank lines and banner bodies are dropped: none of them is
    configuration a policy can assert about, and a banner body is free text whose lines
    would otherwise be read as top-level commands.
    """
    roots: list[Line] = []
    stack: list[tuple[int, Line]] = []
    banner_delim: str | None = None

    for raw in config.splitlines():
        if banner_delim is not None:
            if banner_delim in raw:
                banner_delim = None
            continue

        stripped = raw.strip()
        if not stripped or stripped.startswith("!"):
            continue

        m = _BANNER.match(stripped)
        if m:
            delim = m.group(1)
            # The delimiter may close on the same line: `banner motd ^Chello^C`.
            rest = stripped[m.end():]
            if delim not in rest:
                banner_delim = delim
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        node = Line(_WS.sub(" ", stripped))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if stack:
            stack[-1][1].children.append(node)
        else:
            roots.append(node)
        stack.append((indent, node))

    return roots


def _compile(pattern: str, policy_id: str, key: str) -> re.Pattern[str]:
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise ValueError(
            f"policy {policy_id!r}: {key} {pattern!r} is not a valid regex: {exc}"
        ) from exc


def applies(policy: dict, platform: str, groups: list[str]) -> bool:
    if platform not in policy["platforms"]:
        return False
    wanted = policy.get("groups")
    return not wanted or any(g in groups for g in wanted)


def evaluate(policy: dict, tree: list[Line]) -> dict:
    """Evaluate one policy against a parsed tree. Returns a result record."""
    pid = policy["id"]
    state = policy.get("state", "present")
    config_re = _compile(policy["config"], pid, "config")
    result = {"id": pid, "description": policy.get("description", ""), "state": state}

    if not policy.get("parent"):
        hits = [ln.text for ln in tree if config_re.fullmatch(ln.text)]
        if state == "present":
            ok = bool(hits)
            detail = hits[0] if ok else f"no top-level line matches /{policy['config']}/"
        else:
            ok = not hits
            detail = "absent" if ok else f"found: {', '.join(hits)}"
        return {**result, "compliant": ok, "detail": detail}

    parent_re = _compile(policy["parent"], pid, "parent")
    blocks = [ln for ln in tree if parent_re.fullmatch(ln.text)]

    if state == "present":
        if not blocks:
            return {**result, "compliant": False,
                    "detail": f"no block matches /{policy['parent']}/"}
        missing = [b.text for b in blocks
                   if not any(config_re.fullmatch(c.text) for c in b.children)]
        ok = not missing
        detail = (f"{len(blocks)} block(s) compliant" if ok
                  else f"missing under: {', '.join(missing)}")
        return {**result, "compliant": ok, "detail": detail}

    offending = [f"{b.text} -> {c.text}" for b in blocks for c in b.children
                 if config_re.fullmatch(c.text)]
    ok = not offending
    return {**result, "compliant": ok,
            "detail": "absent" if ok else f"found: {'; '.join(offending)}"}


def check(config: str, policies: list[dict], platform: str,
          groups: list[str] | None = None) -> list[dict]:
    """Evaluate every applicable policy. Policies that do not apply are omitted."""
    platform = platform.rsplit(".", 1)[-1]  # accept cisco.ios.ios as well as ios
    if platform not in PLATFORMS:
        raise ValueError(f"platform {platform!r} is not one of {', '.join(PLATFORMS)}")
    tree = parse(config)
    return [evaluate(p, tree) for p in policies if applies(p, platform, groups or [])]


def compliance_check(config, policies, platform, groups=None):
    """Ansible filter.

    `running_config | compliance_check(policies, ansible_network_os, group_names)`
    """
    try:
        return check(config, policies, platform, groups)
    except ValueError as exc:
        # Imported lazily so the engine and its tests do not need ansible-core.
        from ansible.errors import AnsibleFilterError

        raise AnsibleFilterError(str(exc)) from exc


class FilterModule:
    def filters(self):
        return {"compliance_check": compliance_check}
