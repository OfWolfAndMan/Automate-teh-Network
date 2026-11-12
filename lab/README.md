# Lab substrate

Two layers, because they answer different questions and cost very different amounts.

## Layer 1 — container-backed Linux target (runs anywhere, no images to licence)

`make e2e-linux` starts a Debian container named `lab-web1`, runs
`playbooks/linux/baseline.yml` against it **twice**, and fails unless the second run reports
`changed=0`. That is the property the resource-module rewrite exists to buy, asserted rather
than hoped for:

```bash
make e2e-linux
```

The container is reached over `community.docker.docker`; there is no sshd in it and no
systemd, which is exactly why `baseline.yml` carries no service tasks.

## Layer 2 — containerlab fabric (needs vendor images)

`lab/network.clab.yml` describes the fabric the network playbooks target: two Arista cEOS
nodes and two FRR routers on a management network.

It cannot run without images, and the licence for cEOS is granted per account, not by this
repository. Deploy is therefore guarded: `make lab-up` fails with the exact pull commands
rather than half-building a topology.

| Node | Kind | Image |
|------|------|-------|
| eos1, eos2 | arista_ceos | `ceos:4.31.2F` (Arista account required) |
| rr1, rr2 | linux | `quay.io/frrouting/frr:10.0.2` (free) |

Known limitation, stated plainly: `network_cli` speaks a vendor CLI, so the FRR nodes are
useful for routing-behaviour checks and for the `cli_command` path over `vtysh`, not as
`cisco.ios` targets. A full IOS/NX-OS run needs CML or a licensed image, which this lab does
not assume.
