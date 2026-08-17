# 8x8 Post-Claude Activation Runbook 0.0.1

Status: `READY_FOR_LOCAL_EXECUTION_NOT_EXECUTED`

This runbook activates the Runtime Integration Kernel only after Claude releases or hands off its Termux/Ubuntu write scope.

## Required inputs

1. Completed Claude handoff packet using `runtime_integration/claude_handoff_packet_template.json`.
2. Current lease registry.
3. Exact local repository paths.
4. Current service and database inventory.
5. Rollback location with sufficient free storage.

## Sequence

### Gate A: handoff

Claude must report `COMPLETED` or `HANDOFF_READY`, list all write targets, tests, cleanup, rollback, and unresolved items. Missing evidence means stop.

### Gate B: read-only reconciliation

Run:

```bash
python3 runtime_integration/post_claude_reconciliation.py \
  --handoff CLAUDE_HANDOFF.json \
  --leases ACTIVE_LEASES.json \
  --repo /root/8x8-os \
  --repo /root/8x8-flashpoint-relay \
  --output POST_CLAUDE_RECONCILIATION.json
```

Required result: `READY_FOR_PLAN_ONLY`. Any conflict blocks installation.

### Gate C: plan-only installation

Run the installer without activation. Review the printed paths and backup plan. Do not start a service.

### Gate D: isolated installation

Install into a separate `0.0.1` directory. Preserve previous files and hashes. Emit `INSTALLED_NOT_ACTIVATED`.

### Gate E: read-only canary

Generate one redacted context snapshot. Validate its digest, private-field exclusions, freshness, and Three-Reality fields.

### Gate F: loopback server

Start the read-only state server on `127.0.0.1` only. Confirm mutating HTTP verbs are rejected and no private values are exposed.

### Gate G: coordination canaries

Test overlapping leases, expired heartbeats, malformed missions, bad digests, stale evidence, missing rollback, and event-chain tampering. All must fail closed.

### Gate H: continuity drill

Create a continuity manifest, alter an isolated fixture, prove verification failure, restore it, and prove verification success.

### Gate I: activation receipt

Record exact source commit, installed paths, file hashes, service state, port binding, tests, cleanup, rollback, Claude handoff digest, lease-registry digest, and final reality/evidence state.

## Hard boundaries

This runbook does not authorize production exposure, protected-key use, database mutation, wallet actions, mainnet activity, public deployment, or authority expansion. Every such action requires a separate exact owner gate.
