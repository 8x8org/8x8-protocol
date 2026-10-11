# Device Work Routing and Treasury Settlement v0.1

Status: **DESIGN DRAFT — NOT RELEASED**

## Objective

Translate an enrolled device into a bounded 8x8 node role, select only compatible workloads, meter actual contribution, account for treasury proceeds and costs, and create a separate user reward event.

## Enrollment model

A device may advertise capabilities before enrollment, but it receives no work until a valid consent covers the exact resource, workload class, profile, coordinator, schedule, and destination.

After affirmative enrollment:

- `STANDARD_25` permits automated scheduling within 25% CPU, GPU, and currently available-memory ceilings;
- `ENHANCED_75` permits automated scheduling within separately approved ceilings up to 75%;
- the scheduler always uses the lower of the profile ceiling, device capability, current safety limit, workload request, and local policy limit;
- local interactive use, heat, power, storage, network, policy, pause, and emergency-stop conditions override scheduling.

## Device classification

Devices are classified independently from their marketing surface.

Possible roles:

- `CONTROLLER_ONLY`
- `FOREGROUND_COMPUTE`
- `BACKGROUND_COMPUTE`
- `MINING_ELIGIBLE`
- `REMOTE_MINER`
- `STORAGE_NODE`
- `VALIDATOR_ELIGIBLE`

“All devices accepted” means all supported devices may be inventoried and assigned a safe role. It does not mean every device can profitably mine every proof-of-work asset.

## Platform rules

- Apple App Store and Google Play clients cannot perform local cryptocurrency mining.
- Telegram Mini Apps and ordinary browser pages are lifecycle-limited and cannot promise persistent hidden background work.
- Native desktop and CLI agents may run a signed local service after explicit enrollment.
- Remote ASICs and mining rigs may be controlled after allowlisting, ownership verification, destination review, and safety gates.

## Workload routing

The router admits only allowlisted workloads whose algorithm, network, hardware requirements, legal status, pool or coordinator, treasury destination, expected costs, and reward accounting mode are declared.

Candidate workload classes include:

- `POW_MINING`
- `POS_VALIDATION`
- `AI_INFERENCE`
- `MEDIA_PROCESSING`
- `SOFTWARE_TESTING`
- `INDEXING`
- `RESEARCH_COMPUTE`
- `STORAGE_VERIFICATION`
- `REMOTE_MINER_CONTROL`

Ethereum Mainnet is not eligible for `POW_MINING`. Bitcoin proof-of-work allocations require an approved mining-capable hardware class. CPU, browser, Telegram, and mobile-controller nodes must not be presented as Bitcoin miners unless an exact hardware attestation proves otherwise.

## Treasury destination

A work allocation that may generate an asset requires a treasury destination reference. The reference identifies an approved destination without exposing private keys.

The user consent must disclose:

- the destination and custody model;
- whether proceeds are paid directly by a pool or converted by a provider;
- network, pool, provider, conversion, custody, tax, and operating-cost treatment;
- the ecosystem fee rule;
- the user reward formula and settlement timing;
- volatility, failure, and zero-reward risk;
- dispute and correction procedures.

## Settlement accounting

All quantities use integer atomic units in a declared asset or accounting unit.

A settlement record contains:

1. gross proceeds;
2. pool fee;
3. network fee;
4. provider or conversion fee;
5. custody cost;
6. tax or legally required deduction;
7. direct operating cost;
8. 8x8 ecosystem fee;
9. user reward pool;
10. treasury reserve;
11. pending dispute reserve;
12. rounding remainder.

The components must reconcile exactly. A target fee of 4.88% is represented as 488 basis points and applies only to the transaction class covered by the approved policy. It does not replace network or provider fees.

## Reward separation

A treasury settlement is not automatically a user entitlement. A separate reward event references finalized resource receipts and settlement records. Simulated, measured-unpriced, pending, disputed, off-chain-final, and on-chain-settled states remain distinct.

NFT or token rewards require a canonical asset registry, legal and security gates, sufficient inventory or issuance authority, and an exact release policy. No NFT mystery box, chance-based reward, fixed yield, or guaranteed asset value is created by this protocol.

## Asset registry blocker

The public project currently records nine utility symbols against an intended eight-token model. Work allocations and settlements may use existing external assets or test units, but must not issue or settle a new 8x8 ecosystem asset until the canonical registry conflict is resolved.
