# 8x8 Hybrid Proof Fabric v0.1

Status: **DESIGN DRAFT — NOT RELEASED**

## Purpose

Define a modern proof fabric without pretending every proof type is a blockchain consensus algorithm.

The fabric has three planes:

1. **Consensus and finality plane** — orders and finalizes ledger state.
2. **Contribution and service plane** — proves resources, work, knowledge, availability, and service delivery.
3. **Identity and authority plane** — proves which registered entity, device, agent, or guardian made an attestation or decision.

## Consensus and finality plane

### Proof of Stake with BFT finality

The future 8x8 chain design uses stake-backed validator selection with Byzantine-fault-tolerant finality as its primary consensus target. Validators must have explicit stake, signing, uptime, slashing, key-separation, and recovery policies.

### Bitcoin proof-of-work anchoring

Finalized 8x8 checkpoints may be committed to a Bitcoin-compatible anchoring method after exact protocol selection and audit. Anchoring supplies external timestamp and cumulative-proof-of-work evidence. It does not make the 8x8 chain part of Bitcoin consensus and does not permit 8x8 validators to claim Bitcoin security without measuring the actual anchoring guarantees.

### Proof of Authority

Proof of Authority is permitted only for private development, simulation, disaster-recovery testing, and controlled test networks. It is not the intended public production consensus.

## Contribution and service plane

### Proof of Compute

Proves that a declared computation was executed against bound inputs and code. Required evidence includes workload digest, input commitment, output commitment, execution environment, metering, verifier result, and replay protection.

### Proof of Useful Work

Adds a purpose and independent usefulness test to Proof of Compute. A valid result must establish not only that arithmetic occurred, but that it corresponds to a real allowlisted task with a requester, objective, input provenance, acceptance test, and output consumer. This proof remains research-gated because useful-work systems can otherwise reward meaningless computation shaped to resemble useful tasks.

### Proof of Storage

The 8x8 storage proof family separates:

- **Proof of Replication** — evidence that a node created and holds a unique committed replica;
- **Proof of Spacetime** — recurring evidence that committed data remained stored over an interval;
- **Proof of Availability** — evidence that declared data or coded shares can be retrieved with the promised probability and latency.

Storage rewards require hard quotas, data classification, encryption, deletion, repair, and privacy policies.

### Proof of Service

Proves that a versioned service-level objective was delivered. Evidence may include authenticated request commitments, response commitments, latency, availability window, output acceptance, policy version, and customer or verifier acknowledgement. Raw private request or response bodies must not be placed in public receipts.

### Proof of Knowledge

Proof of Knowledge is a cryptographic or credential-based assertion that a holder possesses a secret, qualification, capability, or approved knowledge claim without necessarily disclosing the underlying secret or private evidence.

It is not a claim that an AI is omniscient. Accepted forms may include:

- zero-knowledge proof-of-knowledge protocols;
- signed verifiable credentials;
- selective-disclosure presentations;
- reproducible examination or challenge receipts.

### Proof of Contribution

Aggregates verified resource and service receipts into a contribution statement. It may reference compute, storage, bandwidth, validation, moderation, testing, research, documentation, or incident-response work. It cannot convert unverified activity into a reward merely by counting events.

### Proof of Reputation

Derives a bounded reputation state from finalized, non-duplicated evidence over time. Reputation is contextual, decays or expires, is challengeable, and cannot authorize its own policy changes. Seraphim Reputation Proof is one application.

### Proof of Time and Ordering

Uses trusted timestamps, monotonic counters, hash chains, checkpoint anchors, or verifiable-delay mechanisms to prove ordering, expiry, and non-replay properties. Time evidence supports other proofs and is not independently treated as useful work.

## Identity and authority plane

### Proof of Device and Runtime Attestation

Uses signed device/runtime evidence and appraisal policies to determine whether a node is in an approved state. The verifier, not the node's self-description, decides whether the evidence is acceptable.

### Proof of Agent Identity

Binds an agent identity to registered keys, model/runtime version, policy digest, session, and authority ceiling. Model names or avatars are not identity proofs.

### Proof of Authorization

Binds an exact action digest to an approving owner or threshold guardian set, scope, expiry, budget, policy version, and replay nonce. Authorization proof does not prove successful execution; execution requires a separate receipt.

## Common proof envelope

Every 8x8 proof receipt contains:

- proof type, class, and schema version;
- issuer, subject, verifier, and relying-party references;
- policy and code digests;
- evidence commitments;
- issue and expiry times;
- nonce and previous-proof linkage;
- verification result and reason codes;
- privacy classification;
- reward eligibility state;
- dispute and revocation state;
- canonical receipt digest.

## Reward boundary

A proof may be:

- `INELIGIBLE`;
- `SIMULATED`;
- `MEASURED_UNPRICED`;
- `ELIGIBLE_PENDING_REVIEW`;
- `FINALIZED_OFFCHAIN`;
- `FINALIZED_ONCHAIN`.

Consensus participation, resource contribution, proof verification, and financial settlement remain separate events.

## FlashTM8 and Seraphim roles

- **FlashTM8** may propose, validate, coordinate, and approve work inside an externally fixed authority policy.
- **Seraphim** may act as a security guardian, proof reviewer, anomaly detector, and incident-response participant.
- Neither identity may expand its own authority, alter guardian thresholds, disable emergency stop, replace owner keys, or issue financial assets through reputation alone.

## Current truth

This specification defines proof semantics and verification boundaries. It does not deploy a blockchain, validator set, Bitcoin anchor, zero-knowledge circuit, storage market, reward system, token, credential, or autonomous owner replacement.
