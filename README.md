# 8x8 Protocol

> **Pre-release public protocol shell — protocol/contracts only, not the current 8x8 interface or deployment authority.**

For the current cross-repository public product state, start with:

- **[8x8 Current Public State](https://github.com/8x8org/.github/blob/main/CURRENT_PUBLIC_STATE.md)**
- **[8x8 User Edition](https://github.com/8x8org/8x8-user-edition)**

This repository is intended to hold the public, implementation-neutral contracts used by 8x8 clients and services. Repository presence or a protocol schema does **not** prove that a browser/PWA, Telegram Mini App, APK, payment rail, token distribution, wallet signer, marketplace, staking/mining reward, or other value-bearing function is live.

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
- unrestricted shell or device-control capability;
- the canonical current user interface.

## Design principles

1. Least authority by default.
2. Explicit, revocable permission scopes.
3. Hash-linked evidence and deterministic verification.
4. Clear separation of requested autonomy, effective authority, and exact action approval.
5. Public claims labeled by evidence state.
6. Fail closed when signatures, receipts, policy, or freshness checks fail.

Current protocol status: **DESIGNED / PRE-RELEASE unless a specific contract carries a newer evidence receipt.**
