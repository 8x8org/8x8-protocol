# 8x8 Public Protocol Boundary

`8x8-protocol` publishes only contracts that are intentionally useful to public clients, integrators and verifiers. A public schema or verifier describes **how to interoperate with an 8x8 product boundary**; it does not publish the private One-Fabric implementation behind that boundary.

## Allowed public material

- implementation-neutral schemas and validation contracts;
- deterministic public receipt/verifier formats;
- consumer-facing examples and conformance fixtures;
- public identity, permission, entitlement and product-surface contracts;
- intentionally public connector/plugin/network adapter manifests;
- public release, provenance and compatibility contracts.

## Not part of this public repository

- agent-to-agent operational handoffs or continuation packets;
- OWNER_ROOT command/control-plane implementation;
- private agent bodies, SOULs, mission queues, leases or execution ingress;
- private memory/context graphs, dormant estate or donor-selection logic;
- credentials, keys, wallet/signing/custody authority or broker internals;
- private deployment, device, incident, rollback or runtime topology;
- proprietary orchestration, parity/frontier or internal benchmark algorithms;
- source sufficient to reproduce the private 8x8 system unless explicitly approved as a separate open-source component.

## Public protocol ≠ open private implementation

The supported model is:

```text
public client / integrator
        ↓
public schema, verifier or API contract
        ↓ authenticated + policy boundary
private 8x8 service implementation
```

A protocol may be public so independent clients can validate compatibility or receipts while the service implementation remains proprietary.

## Historical disclosure

Removing private material from the active branch does not erase earlier public Git history, forks or caches. If a real credential is ever discovered in historical public material, rotate or revoke it; deletion alone is not remediation.
