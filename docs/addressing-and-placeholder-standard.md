# Address and placeholder standard

Two rules, both machine-enforced by `tools/shield/sanitize.py`. They exist because the
2017-2024 corpus published a private key, 28 crackable Cisco type-5 hashes, plaintext
passwords and a live LAN range in a public repository.

## 1. Three address planes

Every IPv4 literal in this repository belongs to exactly one plane. The plane is visible in
the prefix, so a reader can tell private from public at a glance, and the scrub fails on
anything outside all three.

| Plane | Range | Standard | Why |
|-------|-------|----------|-----|
| internal | `10.0.0.0/16` | RFC 1918 | private topology; the last two octets are preserved, so subnet shape and neighbour pairs survive the mapping |
| external | `198.18.0.0/15` | RFC 2544 | anything that must look routable; a /15 gives 512 /24s, enough for a lab internet |
| example | `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` | RFC 5737 | single illustrative addresses in prose |
| example v6 | `2001:db8::/32` | RFC 3849 | all IPv6 |

Structural literals are left alone: loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`,
`fe80::/10`), netmasks, `0.0.0.0`, broadcast, multicast and reserved space. They identify
nothing, and rewriting them breaks configurations without hiding anything.

### The external allocator is corpus-wide

One destination /24 per distinct source /24, allocated by sorting the distinct source
networks and assigning ordinals. Two properties matter, and both are tested:

- **stable across files** — `155.1.0.0/24` becomes the same destination /24 on every chassis,
  so BGP neighbours and static next-hops still refer to the same link;
- **collision-free** — a hash into the plane was measured to fuse 6 of 66 networks into
  shared /24s, which is the same corruption as splitting one network into many.

### Masks move with their addresses

When an address moves into the external plane its prefix length follows, on that line only:
`ip address 112.0.0.1 255.0.0.0` → `ip address 198.18.3.1 255.255.255.0`, and
`permit 112.0.0.0/8` → `permit 198.18.3.0/24`. The cost is honest: an /8 teaching example
becomes a /24. The alternative — a /8 mask on a /24 address — is a command the device
rejects.

## 2. Placeholders, not redaction

| Class | Treatment |
|-------|-----------|
| Cisco type-5 (`$1$…`) | re-hashed from a generated passphrase — the config still parses, the original hash is gone |
| Cisco type-7 | re-encoded from a generated passphrase — decoding one yields `LAB-ONLY-…` |
| plaintext (`enable secret`, `username … secret`, console/vty `password`, TACACS/RADIUS keys) | `LAB-ONLY-<8 hex>` |
| YAML credential fields (`password:`, `enable_secret:`, `vty_pass:`, `psk:`, …) | keyed on the field-name family; paths, booleans and bare numbers are left alone |
| SNMP communities | `LAB-ONLY-<hex>`; factory defaults `public`/`private` are kept, because `no snmp-server community public` is a command that disables the default |
| numeric key ids (`tunnel key 150`) | kept — an identifier, not a passphrase |
| TLS key material | **deleted**, generated at runtime by `generatetls.sh`; a placeholder private key is still a private key |
| personal identifiers | replaced from a deny list held outside this repository |

Values derive from `HMAC-SHA256(seed, class|context)`, so re-running the scrub over an
unchanged tree changes nothing and the mapping is reproducible. The inverse map is written
outside the repository: a published inverse is the scrub undone.

## Operating the scrub

```bash
python3 tools/shield/sanitize.py --self-test       # prove the encoders and allocator
python3 tools/shield/sanitize.py --check .         # report; exit 1 if anything would change
python3 tools/shield/sanitize.py --apply .         # rewrite, delete key material
```

The scrub does not scan its own source: it carries pattern literals and synthetic sample
strings, and scanning it would either rewrite the tool or report its fixtures as leaks.
