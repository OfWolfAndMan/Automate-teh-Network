# Fixtures

Read-only inputs for tests and parsers. Nothing here is an instruction to run, and nothing
here is produced by a playbook any more — the backup role writes to `.artifacts/` at run
time.

| Directory | Contents | Origin |
|-----------|----------|--------|
| `backups/` | 13 device configuration dumps (IOSV1–10, SW1–4, vEOS1–3, C-VX-01–03) | sanitised lab captures, 2017 |
| `configs/` | 4 generated management-switch configurations | sanitised template output, 2017 |

They are retained deliberately (reviewer ruling, 2026-11-11): a backup role without fixtures
is a claim without a test, and these are the only device-shaped inputs this repository has.

Every credential in them is a generated `LAB-ONLY-` placeholder and every address sits in
the internal or external plane — see `docs/addressing-and-placeholder-standard.md`. Do not
"correct" a value here by hand; run `make scrub` and let the tool decide.
