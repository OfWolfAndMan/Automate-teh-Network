#!/usr/bin/env bash
# The compliance playbook, end to end, against the backup fixtures. No device, no vault,
# no docker: this layer runs everywhere, CI included.
#
#   1. run it — expect exactly SW1-SW4 to fail (no-domain-lookup), and everyone else to pass
#   2. the report lists all 17 hosts and agrees with the play recap
#   3. run it again — the report is deterministic, so changed=0
#   4. a policy file in the mini-course's shape is refused at the schema gate
#
# Exit codes: 0 pass, 1 fail.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

INVENTORY=tests/compliance/hosts.yml
PLAYBOOK=playbooks/network/compliance.yml
REPORT=.artifacts/compliance/report.json
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

failed_hosts() {  # failed_hosts <log> -> sorted names whose recap says failed>0
  grep -E '^[A-Za-z0-9]+ +: ok=' "$1" | grep -v 'failed=0' | awk '{print $1}' | sort | xargs
}
total_changed() {
  grep -E '^[A-Za-z0-9]+ +: ok=' "$1" | grep -o 'changed=[0-9]*' | cut -d= -f2 \
    | awk '{s += $1} END {print s + 0}'
}

rm -f "$REPORT"

echo "== pass 1"
ansible-playbook -i "$INVENTORY" "$PLAYBOOK" >"$WORK/p1.log" 2>&1
rc=$?
got=$(failed_hosts "$WORK/p1.log")
echo "   rc=$rc failed: ${got:-none}"
[ "$rc" = "2" ] || { echo "FAIL: expected rc=2 (hosts failed), got $rc"; tail -20 "$WORK/p1.log"; exit 1; }
[ "$got" = "SW1 SW2 SW3 SW4" ] || { echo "FAIL: expected SW1 SW2 SW3 SW4 to fail"; exit 1; }

echo "== report"
python3 - "$REPORT" <<'EOF' || exit 1
import json, sys
report = json.load(open(sys.argv[1]))
assert len(report) == 17, f"expected 17 hosts, got {len(report)}"
bad = sorted(h for h, rs in report.items() if not all(r["compliant"] for r in rs))
assert bad == ["SW1", "SW2", "SW3", "SW4"], bad
for h in bad:
    assert [r["id"] for r in report[h] if not r["compliant"]] == ["no-domain-lookup"], h
print(f"   17 hosts, non-compliant: {' '.join(bad)}")
EOF

echo "== pass 2 (the report must not churn)"
ansible-playbook -i "$INVENTORY" "$PLAYBOOK" >"$WORK/p2.log" 2>&1
changed=$(total_changed "$WORK/p2.log")
echo "   changed=$changed"
[ "$changed" = "0" ] || { echo "FAIL: second pass changed $changed"; exit 1; }

echo "== schema gate"
cat >"$WORK/course.yml" <<'EOF'
---
compliance_policies:
  - name: SSH Version 2
    platform: IOS
    device_types: [router]
    config: ip ssh version 2
    parent: "None"
EOF
ansible-playbook -i "$INVENTORY" "$PLAYBOOK" -e "network_compliance_policy_file=$WORK/course.yml" \
  >"$WORK/p3.log" 2>&1 && { echo "FAIL: a course-shaped policy file was accepted"; exit 1; }
grep -q "Additional properties are not allowed" "$WORK/p3.log" \
  || { echo "FAIL: refused, but not by the schema"; grep -m3 ERROR "$WORK/p3.log"; exit 1; }
echo "   refused by the schema"

echo
echo "PASS: SW1-SW4 non-compliant, report stable, schema enforced"
