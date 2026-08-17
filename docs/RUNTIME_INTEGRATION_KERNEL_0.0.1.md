# 8x8 Runtime Integration Kernel 0.0.1

> Reference implementation for local activation. It does not prove that Termux, Ubuntu, Claude, Hermes, or any private service is currently connected.

## Included

- deterministic Global Context Snapshot publisher;
- redacted live-state generation;
- atomic file-backed lease broker;
- write-target conflict rejection;
- lease heartbeat and release records;
- loopback-only read-only HTTP state server;
- reversible Termux/Ubuntu installation packet;
- CI, syntax checks, deterministic tests, and non-activation verification.

## Local activation sequence

1. Wait for any active Claude or Hermes mutation lease to finish or identify a non-overlapping target.
2. Capture repository, service, package, process, database-schema, storage, port, and scheduler baselines.
3. Run the installer without arguments and archive its plan output.
4. Review the target path and rollback location.
5. Run with `--apply` only under an explicit local installation lease.
6. Confirm the generated receipt says `INSTALLED_NOT_ACTIVATED`.
7. Prepare redacted input JSON for agents, missions, leases, services, repositories, deployments, contradictions, and evidence.
8. Generate `GLOBAL_CONTEXT_SNAPSHOT_0.0.1.json`.
9. Validate its digest and expiry.
10. Start the read-only server on loopback only under a separate activation lease.
11. Verify `GET /healthz`, `/v0.0.1/context`, and `/v0.0.1/live-state`.
12. Verify every mutation method returns HTTP 405.
13. Run conflict canaries with two overlapping leases and prove the second is rejected.
14. Stop the server, verify cleanup, and test restoration from the installer backup.
15. Emit a final activation or rollback receipt.

## Signing boundary

The publisher supports optional HMAC-SHA256 for local integrity testing. HMAC does not establish public asymmetric identity and must not be described as production agent attestation. Production signing requires a signer registry, protected key custody, revocation, rotation, verification policy, and ideally hardware-backed or isolated signing.

Post-quantum and hybrid signatures remain `FUTURE_LAB` until independently reviewed and benchmarked.

## Read-only server

```bash
python runtime_integration/live_state_server.py \
  --context state/GLOBAL_CONTEXT_SNAPSHOT_0.0.1.json \
  --live-state state/LIVE_STATE_0.0.1.json \
  --bind 127.0.0.1 \
  --port 8877
```

The server has no write endpoint and defaults to loopback. Remote exposure requires a separate authenticated transport design and owner gate.

## Lease broker

```bash
python runtime_integration/lease_broker.py --registry state/leases.json acquire candidate.json
python runtime_integration/lease_broker.py --registry state/leases.json heartbeat LEASE_ID
python runtime_integration/lease_broker.py --registry state/leases.json release LEASE_ID --handoff-receipt RECEIPT_SHA256
```

Mutation adapters must call the broker before changing a file, repository, service, database, deployment, credential, port, or canonical registry.

## Completion contract

The runtime integration release unit is complete only when all of the following are evidenced on the target node:

- installation receipt;
- exact file digests;
- local lease and conflict canary;
- context snapshot freshness;
- agent/body/node binding;
- service start receipt;
- loopback and method restrictions;
- event and mission receipt chain;
- no secret or private-row exposure;
- cleanup result;
- rollback test;
- independent post-activation census.

Until those gates pass, the correct state is `IMPLEMENTED_REFERENCE_NOT_LIVE`.
