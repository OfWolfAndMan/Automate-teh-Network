# Contributing

Two rules govern every change to this repository. Both exist because the corpus this
repository replaces was eight years old and had been wrong for most of them.

## Rule 1 — a claim is current only if it was executed

A playbook, command or configuration is *verified* when it has been run against a stated
version on a stated date, and not otherwise. Record the environment in the change itself:

| Status | Means |
|--------|-------|
| `verified` | executed against the stated platform and ansible-core version |
| `partial` | part of it ran; the change says which part did not |
| `unverified` | never run — acceptable to commit, never to describe as working |

Never round `partial` up to `verified` to make a table look better. The label is the
product.

## Rule 2 — nothing published carries a real credential, a real address or a real name

Before a commit that touches inventory, templates or device output:

```bash
make scrub          # tools/shield/sanitize.py --check .
```

The scrub enforces the standard in `docs/addressing-and-placeholder-standard.md`:

- credentials become generated `LAB-ONLY-` placeholders (type-5 re-hashed, type-7
  re-encoded, plaintext replaced)
- key material is **deleted**, never replaced — it is generated at runtime
- addresses are normalised into the internal (`10.0.0.0/16`) or external
  (`198.18.0.0/15`) plane; anything else fails
- personal identifiers are replaced from a deny list that lives **outside** this
  repository (`~/.config/cicero/shield-deny.txt` or `$SHIELD_DENY_FILE`). The list is
  never committed: a deny list inside the tree is a copy of the strings it exists to hide.

A first name or an initialled form (`Anthony W`) is acceptable in a public artifact. The
full legal name is not — not in prose, not in a copyright line, not in commit metadata.

## Commits

- Author and committer on public branches: `OfWolfAndMan <12980405+OfWolfAndMan@users.noreply.github.com>`.
- One change per commit, message states the failure mechanism and the evidence, not the mood.
- Never commit a vault file, a `.retry`, a `collections/` directory or a mapping file
  produced by the scrub.

## Running anything

```bash
make setup       # ansible-core + collections, pinned
make inventory   # parse and graph the inventory
make preflight   # the preflight gates (needs a vault password)
make lint        # yamllint + ruff + ansible-lint + syntax-check, exactly as CI runs them
make scrub       # the SHIELD gate
make pytest      # unit tests: the compliance filter and the examples
make compliance  # the compliance playbook against the fixtures, offline
make show        # show.yml parse-and-save against saved captures, offline
make test        # scrub, inventory, syntax, README index, docs, pytest, compliance, show — no vault, no device
```
