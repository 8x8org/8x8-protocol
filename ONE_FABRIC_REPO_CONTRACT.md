# One-Fabric Repository Contract

Canonical root: `fabric://8x8/core`

## Repository role
Public implementation-neutral contracts, schemas, conformance fixtures and verification formats.

## Current upgrade focus
Add explicit compatibility/versioning policy, conformance matrix, protocol test vectors and evidence-state semantics without implying unreleased product availability.

## Required quality gates
- explicit role, authority and privacy boundary;
- predecessor/successor and dependency links;
- evidence-state labels for present, historical, blocked and future-gated capability;
- reproducible tests or verification;
- no secrets/private raw payloads in ordinary Git;
- scoped agent permissions and verifier separation;
- provenance, receipts and rollback;
- measurable benchmarks with dated baselines;
- `PRESENT != HEALTHY != PRODUCTIVE != VERIFIED`.

## Agent operating contract
Agents may research, document, refactor, test and benchmark under scoped authority. They may maintain stable persona/role metadata, but must not claim human biology, consciousness, unrestricted authority or fabricated evidence.

## Scorecard
Documentation, tests, CI/release health, security, provenance coverage, dependency freshness, performance where relevant, duplicate/superseded surface, rollback readiness and agent-readiness.

## Continuous loop
`DISCOVER -> RECONCILE -> IMPLEMENT -> TEST -> VERIFY -> RECEIPT -> SCORE -> PROMOTE/ROLLBACK -> RESEARCH -> REPEAT`
