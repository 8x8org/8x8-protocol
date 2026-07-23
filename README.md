# 8x8 Protocol

> **Pre-release public protocol shell.**

This repository is intended to hold the public, implementation-neutral contracts used by 8x8 clients and services.

## Planned public contents

- task and receipt schemas;
- capability and permission contracts;
- evidence-state definitions;
- public node-enrollment contracts;
- entitlement and usage-metering schemas;
- deterministic receipt verification;
- SDK examples and conformance fixtures;
- release signatures, SBOMs, and provenance.

## Non-goals

This repository does not contain:

- the private 8x8 control plane;
- owner credentials or signing keys;
- private agents, memory, messages, or logs;
- private provider routing;
- owner wallet authority;
- unrestricted shell or device-control capability.

## Design principles

1. Least authority by default.
2. Explicit, revocable permission scopes.
3. Hash-linked evidence and deterministic verification.
4. Clear separation of requested autonomy, effective authority, and exact action approval.
5. Public claims labeled by evidence state.
6. Fail closed when signatures, receipts, policy, or freshness checks fail.

Current status: **DESIGNED, NOT RELEASED**.
