#!/usr/bin/env bash
# Layer 1 of the lab: a container-backed Linux target, and an idempotence assertion.
#
#   1. start a Debian container with python3 (the docker connection needs an interpreter)
#   2. converge it once  — expect changed > 0, or nothing was proven
#   3. converge it again — expect changed == 0, which is the property resource modules buy
#
# Exit codes: 0 pass, 1 fail, 77 skipped (docker unavailable).
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

CONTAINER=${CONTAINER:-lab-web1}
IMAGE=${IMAGE:-python:3.12-slim}
PLAYBOOK=playbooks/linux/baseline.yml
INVENTORY=inventories/lab/hosts.yml

command -v docker >/dev/null 2>&1 || { echo "SKIP: docker not installed"; exit 77; }
docker info >/dev/null 2>&1 || { echo "SKIP: docker daemon not reachable"; exit 77; }

cleanup() { docker rm -f "$CONTAINER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "== starting $CONTAINER from $IMAGE"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER" "$IMAGE" sleep infinity >/dev/null || exit 1

run_play() {
  local log="$1"
  ansible-playbook -i "$INVENTORY" "$PLAYBOOK" --limit web1 >"$log" 2>&1
  local rc=$?
  if [ $rc -ne 0 ]; then
    echo "ansible-playbook exited $rc:"
    grep -E 'fatal|FAILED' "$log" | head -3
  fi
  return $rc
}

field() {  # field <log> <name> -> the number from the web1 recap line
  grep -E '^web1 +: ok=' "$1" | tail -1 | grep -o "$2=[0-9]*" | cut -d= -f2
}

echo "== pass 1 (converge)"
run_play /tmp/e2e-linux-pass1.log || { echo "FAIL: pass 1 did not run"; exit 1; }
p1c=$(field /tmp/e2e-linux-pass1.log changed)
p1f=$(field /tmp/e2e-linux-pass1.log failed)
echo "   changed=$p1c failed=$p1f"

echo "== pass 2 (must be idempotent)"
run_play /tmp/e2e-linux-pass2.log || { echo "FAIL: pass 2 did not run"; exit 1; }
p2c=$(field /tmp/e2e-linux-pass2.log changed)
p2f=$(field /tmp/e2e-linux-pass2.log failed)
echo "   changed=$p2c failed=$p2f"

echo
if [ "${p1f:-1}" != "0" ] || [ "${p2f:-1}" != "0" ]; then
  echo "FAIL: a pass reported failures"; exit 1
fi
if [ "${p1c:-0}" = "0" ]; then
  echo "FAIL: pass 1 changed nothing, so nothing was proven"; exit 1
fi
if [ "${p2c:-1}" != "0" ]; then
  echo "FAIL: second pass was not idempotent (changed=$p2c)"; exit 1
fi
echo "PASS: converged on pass 1 (changed=$p1c), changed=0 on pass 2"
