# One-Fabric Repository Role Contract

**Project:** ©️8x8 by FlashTM8 ⚡️🌎🤖  
**Canonical logical root:** `fabric://8x8/core`  
**Repository:** `8x8org/8x8-protocol`  
**Primary lifecycle classification:** `AUTHORITATIVE`  
**Contract version:** `ONE_FABRIC_REPOSITORY_ROLE_V1`  
**Recorded:** `2026-09-11 UTC`

## Why this repository exists

Public implementation-neutral interoperability authority for identity, capability, permission, receipt, evidence, entitlement, node, and conformance contracts.

This repository is one bounded organ of **ONE Fabric**. Repository separation is an engineering, security, release, or provenance boundary; it does not create another 8x8 root.

## Authority and ownership

Published versioned public promises and conformance rules; it does not own private implementation details or native-chain internals.

When documentation or code conflicts across repositories, apply this precedence:

1. `horbolsi/8x8` defines overall private One-Fabric architecture and OWNER_ROOT policy.
2. `horbolsi/8x8-blockchain` defines native-chain internals and economic invariants within that policy.
3. `8x8org/8x8-protocol` defines versioned public interoperability promises.
4. Deployment/product repositories consume those authorities.
5. Specialist implementations remain bounded to their declared capability.
6. Backups and dormant donors preserve history but do not override current authority.

## Dependencies and information flow

Private core and specialist implementations may implement it; user-edition consumes it.

A dependency is not automatically active. Source must be adopted, configured, authenticated, granted, started, tested, and independently verified before being labeled productive.

## Runtime placement

Schemas, specifications, SDKs, fixtures, signatures, and conformance tests—not a production service by itself.

The wider physical model is:

- **Termux on S22:** hardware-facing body and Android capability boundary.
- **Ubuntu PRoot:** Linux compute, builds, agents, brokers, databases, and engineering services.
- **`/storage/emulated/0/8x8 OS`:** owner-visible persistent artifacts, archives, media, models, exports, and receipts—not the primary secret store or executable authority.
- **GitHub:** versioned source, policy, CI, releases, and provenance—not live runtime proof.
- **Blockchain:** source plus runtime plus independently operated validators; GitHub presence alone is not mainnet.

## Prohibited responsibilities

Protocol presence does not prove deployment, authentication, payment, signing, token issuance, or productive operation.

Across every repository, raw private keys, seed phrases, live Vault secrets, bearer credentials, and raw biometric templates are forbidden in Git. Agents receive opaque handles and scoped capabilities, never raw custody material.

## Evidence and lifecycle semantics

Use the following state distinctions exactly:

`REGISTERED ≠ REACHABLE ≠ HEALTHY ≠ AUTHENTICATED ≠ GRANTED ≠ LEASED ≠ STARTED ≠ PRODUCTIVE ≠ VERIFIED`

Material claims must be classified as:

- **PAST_PRESERVED:** historical evidence retained with provenance.
- **PRESENT_PROVEN:** freshly verified against a named source/runtime, timestamp, and receipt.
- **FUTURE_GATED:** proposed or implemented work not yet promoted to live authority.

The repository lifecycle classes are:

- **AUTHORITATIVE:** defines a bounded truth domain.
- **IMPLEMENTATION:** implements a bounded capability under authority.
- **DEPLOYMENT:** packages or serves approved capabilities.
- **BACKUP:** preserves recoverable state; never the development root.
- **DORMANT DONOR:** preserves useful historical code/design/evidence for explicit adoption.

## Change and promotion protocol

1. Research current authoritative rules and prior evidence.
2. Census existing files, branches, deployments, and runtime copies.
3. Reconcile conflicts without deleting historical donors.
4. Plan the target authority and rollback.
5. Implement on a review branch.
6. Test the bounded capability.
7. Verify against the actual target runtime.
8. produce a hash-linked receipt.
9. Promote only with explicit authority.

Every adoption from this repository into another must record source repository, source commit, source path, destination, semantic changes, tests, receipt hashes, rollback, and invalidation/freshness rules.

## Current verification boundary

This role contract classifies intent and authority. It does **not** prove that this repository is cloned on the S22, synchronized into Ubuntu PRoot, deployed publicly, authenticated, healthy, or productive. A fresh read-only device and deployment census is required for those claims.
