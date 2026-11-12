#!/usr/bin/env bash
# playbooks/network/show.yml, offline: parse two saved `show version` captures with the same
# ntc-templates parser the live path uses, save the structure as JSON, and prove it.
#
#   1. run it with show_save=true — expect one JSON file per host
#   2. the files hold what the captures say (checked against the text, not the parser)
#   3. run it again — the files are deterministic, so changed=0
#
# The live path (`command:` against a device) is not exercised here; it needs a fabric.
# Exit codes: 0 pass, 1 fail.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

INVENTORY=tests/show/hosts.yml
PLAYBOOK=playbooks/network/show.yml
OUT=$(mktemp -d)
WORK=$(mktemp -d)
trap 'rm -rf "$OUT" "$WORK"' EXIT

run() {
  ansible-playbook -i "$INVENTORY" "$PLAYBOOK" \
    -e 'show_text_file=tests/fixtures/show/{{ inventory_hostname }}_show_version.txt' \
    -e show_save=true -e "show_save_dir=$OUT" >"$1" 2>&1
}
total_changed() {
  grep -E '^[A-Za-z0-9]+ +: ok=' "$1" | grep -o 'changed=[0-9]*' | cut -d= -f2 \
    | awk '{s += $1} END {print s + 0}'
}

echo "== pass 1"
run "$WORK/p1.log" || { echo "FAIL: playbook failed"; tail -20 "$WORK/p1.log"; exit 1; }
echo "   changed=$(total_changed "$WORK/p1.log")"

echo "== saved output"
python3 - "$OUT" <<'EOF' || exit 1
import json, re, sys
from pathlib import Path
out = Path(sys.argv[1])
for host in ("sw1", "sw2"):
    f = out / host / "show_version.json"
    assert f.is_file(), f"missing {f}"
    [rec] = json.loads(f.read_text())
    capture = Path(f"tests/fixtures/show/{host}_show_version.txt").read_text()
    want = re.findall(r"System Serial Number\s+:\s+(\S+)", capture)
    assert rec["hostname"] == host, rec["hostname"]
    assert sorted(rec["serial"]) == sorted(want), (rec["serial"], want)
    print(f"   {host}: hostname ok, {len(want)} stack serials match the capture")
EOF

echo "== pass 2 (must not churn)"
run "$WORK/p2.log" || { echo "FAIL: pass 2 failed"; exit 1; }
changed=$(total_changed "$WORK/p2.log")
echo "   changed=$changed"
[ "$changed" = "0" ] || { echo "FAIL: second pass changed $changed"; exit 1; }

echo
echo "PASS: two captures parsed, saved, and stable"
