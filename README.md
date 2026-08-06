# 8x8 Protocol

> **8x8 OS 0.0.1 Beta · Public protocol reference · No private control-plane authority**

This repository contains public, implementation-neutral contracts and a standard-library reference implementation for evidence-governed human–AI coordination.

## Coordination Kernel 0.0.1

The first bounded protocol release implements:

1. signed-context digest preparation and external-signature fields;
2. append-only hash-linked runtime events;
3. agent/body/node lease validation and write-target conflict detection;
4. proof-carrying mission validation;
5. redacted read-only estate collection;
6. contradiction validation and resolution-receipt requirements;
7. evidence-freshness evaluation;
8. fail-closed public projection;
9. continuity manifests and restore-integrity verification;
10. shared objects for agent passports, promotion gates, rollback records, public claims, capabilities and policy decisions.

The reference implementation is in [`coordination_kernel/`](coordination_kernel/). It uses only the Python standard library and does not read secrets, private messages, wallet data or database rows.

## Quick validation

```bash
python -m unittest discover -s tests -v
python coordination_kernel/coordination_kernel.py --help
```

Examples:

```bash
python coordination_kernel/coordination_kernel.py context-validate context.json
python coordination_kernel/coordination_kernel.py lease-check candidate-lease.json active-leases.json
python coordination_kernel/coordination_kernel.py mission-validate mission.json --context context.json --leases active-leases.json
python coordination_kernel/coordination_kernel.py event-append events.jsonl event.json
python coordination_kernel/coordination_kernel.py freshness-check evidence.json
python coordination_kernel/coordination_kernel.py project-public private-state.json coordination_kernel/policy/public-projection-policy-0.0.1.json public-state.json
python coordination_kernel/coordination_kernel.py continuity-create continuity.json file-a file-b
python coordination_kernel/coordination_kernel.py continuity-verify continuity.json
```

Read-only estate snapshot:

```bash
python coordination_kernel/read_only_collector.py \
  --repo /path/to/repository \
  --output estate-snapshot.json
```

## Three-Reality protocol

- `PRIVATE_PAST`: private operational history, memory, evidence, recovery truth and current sovereign runtime observations.
- `PUBLIC_PRESENT`: reviewed, privacy-safe, evidence-backed public 0.0.1 Beta projection.
- `FUTURE_LAB`: research, simulations, candidates and unpromoted designs.
- `PROTECTED_BETA`: reversible promotion state between Future Lab and Public Present, not a fourth reality.

## Cryptographic boundary

The reference implementation provides deterministic canonical JSON and SHA-256 digest chains. It deliberately does not manage private keys or pretend a digest alone is an identity signature. Production deployments must bind digests to an approved external signer, protected key custody, revocation, rotation, algorithm identifiers and verification policy.

Post-quantum and hybrid cryptography remain `FUTURE_LAB` until independently reviewed and interoperably tested.

## Public contents

- mission and receipt contracts;
- capability and permission contracts;
- evidence-state and freshness definitions;
- lease and conflict rules;
- context, event and contradiction contracts;
- public projection policy;
- continuity and rollback records;
- SDK examples and conformance tests;
- release signatures, SBOM and provenance direction.

## Non-goals

This repository does not contain or grant:

- the private 8x8 control plane;
- owner credentials or signing keys;
- private agents, memory, messages or logs;
- private provider routing;
- owner wallet authority;
- unrestricted shell or device control;
- production deployment authority;
- whole-system completion or stability claims.

## Design principles

1. Least authority by default.
2. Explicit, expiring and revocable permissions.
3. Hash-linked evidence and deterministic verification.
4. Agent, body, node, mission and context binding.
5. Public claims labeled by evidence state and freshness.
6. No write without a valid nonconflicting lease.
7. No completion without tests, cleanup, rollback and a final receipt.
8. Fail closed when signatures, policy, freshness or evidence checks fail.

Current status: **IMPLEMENTED REFERENCE, PROTECTED BETA, NOT PRODUCTION-ACTIVATED**.
