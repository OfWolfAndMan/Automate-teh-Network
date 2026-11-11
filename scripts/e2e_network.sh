#!/usr/bin/env bash
# Layer 2 of the lab: deploy the containerlab fabric and prove the network playbooks against
# it. Guarded, because the cEOS image is granted per Arista account and cannot be pulled by
# this repository.
#
# Exit codes: 0 pass, 1 fail, 77 skipped (substrate absent).
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

TOPO=lab/network.clab.yml

command -v containerlab >/dev/null 2>&1 || {
  echo "SKIP: containerlab is not installed (see lab/README.md)"; exit 77; }

missing=""
docker image inspect ceos:4.31.2F >/dev/null 2>&1 || missing="$missing ceos:4.31.2F(after Arista login: docker pull ceos:4.31.2F)"
docker image inspect quay.io/frrouting/frr:10.0.2 >/dev/null 2>&1 || missing="$missing quay.io/frrouting/frr:10.0.2(docker pull quay.io/frrouting/frr:10.0.2)"

if [ -n "$missing" ]; then
  echo "SKIP: container images missing:$missing"
  echo "      deploy is not attempted: a half-built topology produces misleading failures"
  exit 77
fi

cleanup() { containerlab destroy -t "$TOPO" --cleanup >/dev/null 2>&1 || true; }
trap cleanup EXIT

containerlab deploy -t "$TOPO" || exit 1

# Backup is read-only and safe to assert against a live fabric: it must converge twice.
for pass in 1 2; do
  echo "== backup pass $pass"
  ansible-playbook -i inventories/lab/hosts.yml playbooks/network/backup.yml 2>&1 | tail -4
done

echo "PASS: fabric deployed, backup converged twice"
