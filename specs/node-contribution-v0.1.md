# 8x8 Node Contribution Protocol v0.1

Status: **DESIGN DRAFT — NOT RELEASED**

## Purpose

Define implementation-neutral contracts for optional user-owned nodes to contribute bounded resources to an 8x8 network while preserving user control, privacy, security, revocation, and evidence.

This specification does not create a token, coin, wallet, subscription, payment, investment, mining pool, or reward entitlement.

## Core principles

1. Installation grants no contribution authority.
2. Each resource class requires separate affirmative consent.
3. Consent is purpose-limited, capped, revocable, expiring, and receipted.
4. User credentials remain outside contribution data and reward calculations.
5. Unknown workloads and ambiguous permissions fail closed.
6. Every accepted workload is bound to code, policy, consent, and receipt digests.
7. The user can pause or revoke work locally.
8. Mobile clients do not perform cryptocurrency mining on the mobile device.
9. Precise location is not a default node resource.
10. Rewards remain separate from measured contribution and require additional gates.

## Resource classes

- `CPU`
- `GPU`
- `STORAGE`
- `BANDWIDTH`
- `TELEMETRY`
- `REMOTE_MINER_MANAGEMENT`
- `PRECISE_LOCATION`
- `REWARDS`

Each class uses a separate consent record. A consent for one class cannot authorize another.

## Required consent properties

A node consent contains:

- consent and node identifiers;
- resource class;
- purpose and workload-class allowlist;
- issue, activation, expiration, and revocation timestamps;
- resource ceilings and schedule;
- network, battery, thermal, and storage restrictions where applicable;
- allowed coordinators and destinations;
- data classification and retention;
- reward participation state;
- local pause and kill-switch requirements;
- policy digest and receipt destination;
- user approval evidence.

## Workload admission

A workload is accepted only when:

- coordinator identity is authenticated;
- manifest signature and package digest pass;
- workload class is allowlisted;
- consent is active and unexpired;
- requested resources remain below all ceilings;
- data classification is permitted;
- destination and network policy pass;
- local safety checks pass;
- the kill switch is clear;
- receipt storage is available.

A rejection produces a receipt with no workload execution.

## Resource receipt

A resource receipt records measured facts, not promotional value. It includes consent, workload, coordinator, code digest, policy digest, timestamps, resource units, ceilings, result, interruption reason, reward stage, and hash linkage.

The receipt excludes secret values, unrelated personal files, raw private messages, and precise location coordinates.

## Reward stages

- `NONE`
- `SIMULATED`
- `MEASURED_UNPRICED`
- `OFFCHAIN_PENDING`
- `OFFCHAIN_FINAL`
- `ONCHAIN_PENDING`
- `ONCHAIN_SETTLED`

Only `ONCHAIN_SETTLED` may reference a verified transaction identifier. No stage guarantees monetary value, liquidity, profit, APY, or appreciation.

## Mobile and mining boundary

Mobile applications may display or control separately owned remote mining hardware only after explicit authorization. They must not mine cryptocurrency on the mobile device. Payout-destination changes, pool changes, firmware changes, and power-limit changes require separate high-impact approval and receipts.

## Location boundary

Precise location requires separate affirmative consent for a service directly requested by the user. Node enrollment, subscription, rewards, or another permission cannot imply location consent. Location data may not appear in public receipts. Rewarding location is outside v0.1 and disabled.

## BYOK boundary

Schemas use opaque secret references only. Implementations must not place API keys, wallet keys, passwords, cookies, private tokens, or provider credentials in consent records, workload manifests, resource receipts, reward events, public logs, or public repositories.

## Compatibility and versioning

Every object includes a schema identifier. Breaking changes require a new schema version. Implementations must reject unknown major versions and preserve the original object digest when translating compatible minor versions.
