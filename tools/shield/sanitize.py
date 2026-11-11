#!/usr/bin/env python3
"""Deterministic placeholder generation for a public network-automation corpus.

Version 1.1 — after Fred's review (2026-11-11), which broke A1 and A2 by execution:

  A1  plaintext credentials (`enable secret <pw>`, `username X secret <pw>`,
      `password <pw>`, `key <psk>`, YAML `password:` / `key:`) survived v1.0's
      hash-only patterns.
  A2a `/16` masks were never re-coupled, producing `ip route 198.18.15.0 255.255.0.0`
      — an address and mask IOS rejects as inconsistent.
  A2b the allocator was per-file and stateful, so the same link mapped to different
      /24s on adjacent chassis and every inter-chassis BGP session was severed.
  Gap  the covering letter promised deletion of key material; v1.0 had no unlink.

Two jobs.

1. SECRETS  every credential-shaped string becomes a generated value that is
   syntactically valid but carries no history: type-5 re-hashed, type-7 re-encoded
   (decode one and you get LAB-ONLY-...), plaintext secrets and YAML keys set to
   LAB-ONLY-<hex>, factory-default SNMP communities kept, key material DELETED.

2. ADDRESSES  every IPv4 and IPv6 literal is normalised into one of three declared
   planes, distinguishable by prefix and by machine check:

     INTERNAL  10.0.0.0/16     RFC 1918  last two octets kept
     EXTERNAL  198.18.0.0/15   RFC 2544  ONE /24 PER SOURCE /24, CORPUS-WIDE
     EXAMPLE   RFC 5737 / RFC 3849      left unchanged when already present

   The external allocation is corpus-wide and order-independent: every distinct
   source /24 in the tree is collected first, sorted, and given a stable index, so
   `155.1.0.0/24` becomes the same destination /24 in every file. A hash-based
   allocation (the reviewer's suggested fix) was measured to collide: 66 distinct
   networks into 512 slots gave 6 aliases, which fuses distinct networks — a
   different corruption of the same topology.

Determinism: values derive from HMAC-SHA256(seed, class|context); a second --apply
changes nothing.

Usage:
  sanitize.py --check ROOT     report only, exit 1 if anything would change
  sanitize.py --apply ROOT     rewrite in place, delete key material, write mapping
  sanitize.py --self-test      prove the encoders, allocator and coupling
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SEED = os.environ.get("LAB_SEED", "ateh-lab-2026-11").encode()
LAB_ONLY = "LAB-ONLY"

PRIVATE_SLAB = "10.0"                  # 10.0.0.0/16
BENCHMARK = (198, 18)                  # 198.18.0.0/15
BENCHMARK_SLOTS = 2 * 256
TLS_KEY_MATERIAL = (
    "Playbooks/Linux/roles/nginx/files/nginx.key",
    "Playbooks/Linux/roles/nginx/files/nginx.crt",
)

# ---------------------------------------------------------------- generators


def ph(kind: str, context: str, n: int = 8) -> str:
    return hmac.new(SEED, f"{kind}|{context}".encode(), hashlib.sha256).hexdigest()[:n]


T7_KEY = "dsfd;kfoA,.iyewrkldJKDHSUB"


def type7_encode(plain: str, index: int = 0) -> str:
    out = [f"{index:02d}"]
    for i, ch in enumerate(plain):
        out.append(f"{ord(ch) ^ ord(T7_KEY[(index + i) % len(T7_KEY)]):02X}")
    return "".join(out)


def type7_decode(enc: str) -> str:
    idx = int(enc[:2])
    body = enc[2:]
    return "".join(
        chr(int(body[i : i + 2], 16) ^ ord(T7_KEY[(idx + i // 2) % len(T7_KEY)]))
        for i in range(0, len(body), 2)
    )


T5_RE = re.compile(r"^\$1\$[A-Za-z0-9./]{1,8}\$[A-Za-z0-9./]{22}$")


def type5_hash(passphrase: str, salt: str) -> str:
    res = subprocess.run(
        ["openssl", "passwd", "-1", "-salt", salt, passphrase],
        capture_output=True, text=True, check=True,
    )
    out = res.stdout.strip()
    if not T5_RE.match(out):
        raise RuntimeError(f"openssl produced an unexpected type-5 form: {out!r}")
    return out


# ---------------------------------------------------------------- addresses


def _is_netmask(o: list[int]) -> bool:
    val = (o[0] << 24) | (o[1] << 16) | (o[2] << 8) | o[3]
    inv = val ^ 0xFFFFFFFF
    return (inv & (inv + 1)) == 0 and val not in (0, 0xFFFFFFFF)


def classify(ip: str) -> str:
    try:
        o = [int(p) for p in ip.split(".")]
    except ValueError:
        return "invalid"
    if len(o) != 4 or any(p > 255 for p in o):
        return "invalid"
    if ip in ("0.0.0.0", "255.255.255.255"):
        return "structural"
    if _is_netmask(o):
        return "netmask"
    if o[0] == 127:
        return "loopback"
    if o[0] == 169 and o[1] == 254:
        return "linklocal"
    if (o[0] == 192 and o[1] == 0 and o[2] == 2) or \
       (o[0] == 198 and o[1] == 51 and o[2] == 100) or \
       (o[0] == 203 and o[1] == 0 and o[2] == 113):
        return "example"
    if o[0] == 198 and o[1] in (18, 19):
        return "benchmark"
    if o[0] == 10 or (o[0] == 172 and 16 <= o[1] <= 31) or (o[0] == 192 and o[1] == 168):
        return "internal"
    if o[0] == 0 or o[0] >= 224:
        return "reserved"
    return "external"


class Allocator:
    """Corpus-wide, order-independent mapping of source /24s into 198.18.0.0/15.

    The map is built once from the whole corpus (sorted, so it is deterministic and
    independent of file order and of which file is touched first), which is what keeps
    a link at the same address on both of its chassis.
    """

    def __init__(self, src_nets: set[str] | None = None) -> None:
        self.map: dict[str, str] = {}
        for idx, net in enumerate(sorted(src_nets or ())):
            if idx >= BENCHMARK_SLOTS:
                raise RuntimeError("external plane exhausted: >512 distinct source /24s")
            self.map[net] = f"{BENCHMARK[0]}.{BENCHMARK[1] + (idx // 256)}.{idx % 256}"

    def dest_prefix(self, src_net: str) -> str:
        if src_net not in self.map:            # a network met after construction
            idx = len(self.map)
            if idx >= BENCHMARK_SLOTS:
                raise RuntimeError("external plane exhausted")
            self.map[src_net] = f"{BENCHMARK[0]}.{BENCHMARK[1] + (idx // 256)}.{idx % 256}"
        return self.map[src_net]

    def map_ip(self, ip: str, kind: str) -> str:
        o = [int(p) for p in ip.split(".")]
        if kind == "internal":
            return f"{PRIVATE_SLAB}.{o[2]}.{o[3]}"
        if kind == "external":
            return f"{self.dest_prefix('.'.join(map(str, o[:3])))}.{o[3]}"
        return ip


IP_RE = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])")
WILDCARD_RE = re.compile(r"(?<![\d.])0\.(?:255\.){2}255(?![\d.])|(?<![\d.])0\.0\.255\.255(?![\d.])")
SLASH_PREFIX_RE = re.compile(r"(?<=[\d])/([1-9]|[12][0-9])(?![0-9])")
V6_RE = re.compile(r"(?<![\w:.])((?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}(?:/\d{1,3})?)(?![\w:.])")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")


def map_v6(tok: str) -> str:
    """Global unicast -> 2001:db8::/32, keeping subnet id and interface (RFC 3849)."""
    addr, _, plen = tok.partition("/")
    low = addr.lower()
    if TIME_RE.match(tok) or low.startswith(("fe80", "::1", "ff0", "::", "2001:db8")):
        return tok
    parts = low.split(":")
    if len(parts) < 3:
        return tok
    rest = ":".join(parts[2:])
    new = "2001:db8:" + rest if rest else "2001:db8::"
    return new + ("/" + plen if plen else "")


# ---------------------------------------------------------------- secrets

SECRET_PATTERNS = [
    # hashed forms first: they are the most specific
    ("cisco_type5", re.compile(r"(?P<pre>\b(?:enable\s+secret|secret|password)\s+5\s+)(?P<val>\$1\$[A-Za-z0-9./]{1,8}\$[A-Za-z0-9./]{22})")),
    ("cisco_type7", re.compile(r"(?P<pre>\b(?:key|password)\s+7\s+)(?P<val>[0-9A-Fa-f]{4,})")),
    # plaintext device credentials (A1)
    ("cisco_plain_secret", re.compile(r"(?P<pre>\benable\s+secret\s+)(?!(?:5|7)\b)(?P<val>[^\s{!]+)")),
    ("cisco_user_secret", re.compile(r"(?P<pre>\busername\s+\S+\s+(?:secret|password)\s+)(?!(?:5|7)\b)(?P<val>[^\s{!]+)")),
    ("cisco_plain_password", re.compile(r"(?P<pre>^\s*password\s+)(?!(?:5|7)\b)(?P<val>[^\s{!]+)")),
    ("cisco_key_string", re.compile(r"(?P<pre>\bkey-string\s+(?:7\s+)?)(?P<val>[^\s!]+)")),
    ("cisco_standalone_key", re.compile(r"(?P<pre>(?:^|\s)key\s+)(?!(?:7|chain|string|config)\b)(?P<val>[A-Za-z0-9@#$_!.\-]+)")),
    # SNMP
    ("snmp_community", re.compile(r"(?P<pre>snmp-server\s+community\s+)(?!\{)(?P<val>[^\s\"{]+)")),
    ("snmp_host_community", re.compile(r"(?P<pre>snmp-server\s+host\s+\S+\s+)(?!version|informs|traps|vrf|udp-port)(?P<val>[A-Za-z0-9@._:-]+)")),
    # Ansible / YAML
    # Ansible / YAML — keyed on the KEY NAME, not on an enumeration of field names.
    # `enable_secret:`, `vty_pass:`, `psk:`, `console_pass:`, `community:` and their
    # cousins are one class; enumerating them is how v1.0 left four of them behind.
    ("yaml_credential", re.compile(
        r"(?P<pre>^\s*[A-Za-z0-9_.\-]*(?:pass|secret|key|psk|community|token)[A-Za-z0-9_.\-]*\s*:\s*[\"']?)"
        r"(?!\{)(?P<val>[^\"'\s#}]+)", re.IGNORECASE)),
    ("ansible_ssh_pass", re.compile(r"(?P<pre>ansible_ssh_pass\s*=\s*)(?P<val>\S+)")),
    ("ansible_become_pass", re.compile(r"(?P<pre>ansible_become_pass\s*=\s*)(?P<val>\S+)")),
    ("ansible_password", re.compile(r"(?P<pre>ansible_password\s*[=:]\s*)(?P<val>\S+)")),
    ("radius_key", re.compile(r"(?P<pre>radius-server\s+key\s+(?:7\s+)?)(?P<val>\S+)")),
    ("tacacs_key", re.compile(r"(?P<pre>tacacs-server\s+key\s+(?:7\s+)?)(?P<val>\S+)")),
]

BINARY_SKIP = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".bundle"}
DEFAULT_COMMUNITIES = {"public", "private"}
COMMENT_PREFIXES = ("#", "--", "<!--")
DENY_FILE = os.environ.get("SHIELD_DENY_FILE", os.path.expanduser("~/.config/cicero/shield-deny.txt"))


def load_deny_terms() -> list[str]:
    try:
        raw = Path(DENY_FILE).read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    return [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.startswith("#")]


def scrub_identity(line: str, terms: list[str], stats: dict, mapping: dict) -> str:
    out = line
    for t in terms:
        pat = re.compile(r"(?<![\w.-])" + re.escape(t) + r"(?![\w.-])", re.IGNORECASE)
        if pat.search(out):
            rep = "devops@example.com" if "@" in t else "devops"
            mapping.setdefault("identity", {})[t] = rep
            stats["identity"] = stats.get("identity", 0) + 1
            out = pat.sub(rep, out)
    return out


def scrub_secrets(line: str, relpath: str, stats: dict, mapping: dict) -> str:
    if line.lstrip().startswith(COMMENT_PREFIXES):
        return line
    out = line
    for name, rx in SECRET_PATTERNS:
        def sub(m, name=name):
            raw = m.group(0)
            if "{" in raw or "}" in raw:       # a Jinja expression is never a literal
                return raw
            pre, val = m.group("pre"), m.group("val")
            if name.startswith("snmp_community") and val.strip("'\"").lower() in DEFAULT_COMMUNITIES:
                stats["snmp_default_kept"] = stats.get("snmp_default_kept", 0) + 1
                return raw
            if val.lower().startswith("lab-only"):
                return raw
            if name == "cisco_standalone_key" and re.fullmatch(r"\d+", val):
                # a key identifier (`key 1`, `tunnel key 150`) is not a passphrase; rewriting
                # it produces a command the device rejects
                stats["key_id_kept"] = stats.get("key_id_kept", 0) + 1
                return raw
            if name == "yaml_credential":
                low = val.strip("'\"").lower()
                if (low in {"true", "false", "yes", "no", "none", "null", "~"}
                        or re.fullmatch(r"[\d.]+", low)
                        or "/" in low
                        or low.endswith((".yml", ".yaml", ".j2", ".cfg", ".sh", ".conf",
                                         ".py", ".txt", ".json", ".pem", ".crt", ".key"))):
                    return raw
            ctx = f"{name}|{relpath}|{stats.get(name, 0)}"
            if name == "cisco_type5":
                new = type5_hash(f"{LAB_ONLY}-{ph('t5pass', ctx, 10)}", ph("t5salt", ctx, 8))
            elif name == "cisco_type7":
                idx = int(val[:2]) if val[:2].isdigit() else 0
                new = type7_encode(f"{LAB_ONLY}-{ph('t7pass', ctx, 10)}", idx % 16)
            else:
                new = f"{LAB_ONLY}-{ph(name, ctx, 8)}"
            mapping.setdefault(name, {}).setdefault(val, new)
            stats[name] = stats.get(name, 0) + 1
            return pre + new
        out = rx.sub(sub, out)
    return out


def scrub_addresses(line: str, alloc: Allocator, stats: dict, mapping: dict) -> str:
    touched_external = False

    def sub(m: re.Match) -> str:
        nonlocal touched_external
        ip = m.group(1)
        kind = classify(ip)
        stats[f"ip_{kind}"] = stats.get(f"ip_{kind}", 0) + 1
        new = alloc.map_ip(ip, kind)
        if kind == "external" and new != ip:
            touched_external = True
        if new != ip:
            mapping.setdefault("ip", {}).setdefault(ip, new)
        return new

    out = IP_RE.sub(sub, line)

    def v6_sub(m: re.Match) -> str:
        tok = m.group(1)
        new = map_v6(tok)
        if new != tok:
            stats["ip_v6"] = stats.get("ip_v6", 0) + 1
            mapping.setdefault("ip_v6", {}).setdefault(tok, new)
            return m.group(0).replace(tok, new, 1)
        return m.group(0)

    out = V6_RE.sub(v6_sub, out)

    if touched_external:
        # every mask on this line must match the /24 the address just moved into
        out = IP_RE.sub(
            lambda m: "255.255.255.0" if classify(m.group(1)) == "netmask" else m.group(1), out)
        out = WILDCARD_RE.sub("0.0.0.255", out)
        out = SLASH_PREFIX_RE.sub("/24", out)
    return out


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file() or ".git" in p.parts or "__pycache__" in p.parts:
            continue
        # the scrub's own source carries pattern literals and sample strings; scanning it
        # would either rewrite the tool or report its fixtures as leaks
        if p.name == "sanitize.py" or "tools/shield" in p.parts:
            continue
        if p.suffix.lower() in BINARY_SKIP:
            continue
        yield p


def collect_external_nets(root: Path) -> set[str]:
    nets: set[str] = set()
    for p in iter_files(root):
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in IP_RE.finditer(text):
            if classify(m.group(1)) == "external":
                nets.add(".".join(m.group(1).split(".")[:3]))
    return nets


def run(root: Path, apply: bool, mapping_path: Path) -> int:
    stats: dict = {}
    mapping: dict = {}
    changed: list[str] = []
    files = list(iter_files(root))
    deny = load_deny_terms()
    alloc = Allocator(collect_external_nets(root))      # corpus-wide, before any write

    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = str(p.relative_to(root))
        new = "".join(
            scrub_identity(scrub_addresses(scrub_secrets(ln, rel, stats, mapping), alloc, stats, mapping),
                           deny, stats, mapping)
            for ln in text.splitlines(keepends=True)
        )
        if new != text:
            changed.append(rel)
            if apply:
                p.write_text(new, encoding="utf-8")

    removed = []
    for rel in TLS_KEY_MATERIAL:
        p = root / rel
        if p.exists():
            removed.append(rel)
            if apply:
                p.unlink()
                stats["key_material_deleted"] = stats.get("key_material_deleted", 0) + 1

    report = {
        "root": str(root),
        "mode": "apply" if apply else "check",
        "files_scanned": len(files),
        "files_changed": len(changed),
        "changed": changed,
        "key_material_removed": removed,
        "external_nets_allocated": len(alloc.map),
        "stats": dict(sorted(stats.items())),
    }
    print(json.dumps(report, indent=2))
    if apply and mapping:
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        mapping_path.write_text(json.dumps(mapping, indent=2, sort_keys=True))
        print(f"mapping written: {mapping_path} (outside the repo on purpose)", file=sys.stderr)
    return 1 if (changed or removed) and not apply else 0


def self_test() -> int:
    ok = True
    pw = "LAB-ONLY-selftest"
    for idx in (0, 1, 7, 15):
        good = type7_decode(type7_encode(pw, idx)) == pw
        print(f"type7 idx={idx:2d} roundtrip={'ok' if good else 'FAIL'}")
        ok &= good
    h = type5_hash(pw, "abcdefgh")
    print(f"type5 format={'ok' if T5_RE.match(h) else 'FAIL'} deterministic={h == type5_hash(pw, 'abcdefgh')}")
    ok &= bool(T5_RE.match(h))

    nets = {"155.1.0.0", "155.1.108.0", "112.0.0.0", "155.1.79.0"}
    a1 = Allocator(nets)
    a2 = Allocator(set(sorted(nets, reverse=True)))
    same = all(a1.dest_prefix(n) == a2.dest_prefix(n) for n in nets)
    uniq = len({a1.dest_prefix(n) for n in nets}) == len(nets)
    print(f"allocator order-independent={same} collision-free={uniq}")
    ok &= same and uniq

    line = " ip address 112.0.0.1 255.0.0.0"
    ok &= "255.255.255.0" in scrub_addresses(line, a1, {}, {})
    l16 = "ip route 155.1.0.0 255.255.0.0 155.1.108.8"
    out16 = scrub_addresses(l16, a1, {}, {})
    good16 = "255.255.0.0" not in out16 and out16.count("255.255.255.0") == 1
    print(f"/16 coupling: {out16.strip()!r} {'ok' if good16 else 'FAIL'}")
    ok &= good16
    pl = "ip prefix-list X seq 5 permit 112.0.0.0/8"
    good_pl = "/24" in scrub_addresses(pl, a1, {}, {})
    print(f"prefix coupling {'ok' if good_pl else 'FAIL'}")
    ok &= good_pl

    for v6, want in {
        "2001:150:10:10::10/128": "2001:db8:10:10::10/128",
        "2001:150:1:1::1": "2001:db8:1:1::1",
        "fe80::1": "fe80::1",
        "2001:db8:99::1": "2001:db8:99::1",
        "16:27:07": "16:27:07",
    }.items():
        got = map_v6(v6)
        print(f"{v6:24s} -> {got:26s} {'ok' if got == want else 'FAIL want ' + want}")
        ok &= got == want

    for name, line, must in [
        ("enable secret", "enable secret SAMPLE-value-one", "LAB-ONLY"),
        ("username", "username sampleuser secret SAMPLE-value-two", "LAB-ONLY"),
        ("vty password", " password SAMPLE-value-three", "LAB-ONLY"),
        ("tacacs key", " key SAMPLE-value-four", "LAB-ONLY"),
        ("yaml pw", "  password: SAMPLE-value-five", "LAB-ONLY"),
        ("yaml key", "      key: SAMPLE-value-six", "LAB-ONLY"),
    ]:
        out = scrub_secrets(line, "f", {}, {}).strip()
        good = must in out
        print(f"plaintext {name:16s} {out!r} {'ok' if good else 'FAIL'}")
        ok &= good

    keep = scrub_secrets(" no snmp-server community public", "f", {}, {}).strip()
    print(f"default community kept: {'ok' if keep == 'no snmp-server community public' else 'FAIL'}")
    ok &= keep == "no snmp-server community public"
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", metavar="ROOT", nargs="?", const=".")
    g.add_argument("--apply", metavar="ROOT", nargs="?", const=".")
    g.add_argument("--self-test", action="store_true")
    ap.add_argument("--mapping", default=os.path.expanduser("~/.hermes/state/ateh-sanitize-map.json"))
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.check:
        return run(Path(a.check).resolve(), False, Path(a.mapping))
    return run(Path(a.apply).resolve(), True, Path(a.mapping))


if __name__ == "__main__":
    raise SystemExit(main())
