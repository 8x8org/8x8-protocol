# 8x8 Commercial Product Protocol V1

Status: **PUBLIC CONTRACTS IMPLEMENTED ON A FEATURE BRANCH; PRODUCTION NOT AUTHORIZED**

## Product boundary

8x8 has two product classes:

1. **Private owner product** for FlashTM8, trusted agent teams, private memory, operations, receipts, connectors and exact approvals.
2. **Public user product** for web, mobile, CLI, SDK, MCP, ChatGPT-app style integrations and Telegram Mini App access under least authority.

The public product must never inherit private root authority, owner credentials, private memories, wallet signing, unrestricted local tools or hidden operator routes.

## Entitlement

- Trial duration: **88 minutes**, represented as exactly **5,280 server-metered seconds**.
- Intended paid price: **USD 8.88**.
- Billing cadence remains an explicit owner decision. Supported contract values are one-time, monthly, quarterly, yearly or usage-pack.
- Browser clocks are not authoritative.
- Usage and entitlement transitions require deterministic receipts.
- Anonymous duplicate-trial abuse must be rate-limited and reviewable.

## Existing wallet truth

The owner confirmed existing Bitcoin and Monero wallets.

Current classification:

- `OWNER_CONFIRMED_NOT_INSPECTED`
- no address stored in this public repository
- no balance queried
- no seed, private key, spend key, descriptor secret or credential accessed
- no signing or spending authority granted

## Bitcoin rail

Recommended architecture:

- non-custodial invoices;
- BTCPay Server or an equivalent independently reviewed adapter;
- unique invoice address per payment;
- watch-only descriptor or xpub reference;
- no private key in the public application;
- explicit confirmation and expiry policy;
- refunds separately exact-gated;
- Lightning enabled only after a dedicated liquidity, availability and failure-recovery canary.

## Monero rail

Recommended architecture:

- unique subaddress per invoice;
- view-only monitoring where feasible;
- wallet RPC bound to loopback or an authenticated private network;
- no spend key in the public application;
- no unauthenticated remote RPC;
- privacy-aware accounting and refund handling;
- jurisdiction, tax, sanctions and privacy review before public activation.

## Other networks

Planned adapters:

- Ethereum
- BNB Smart Chain
- Solana
- TON
- Pi Network

A listed adapter is not proof that a token, contract, mint, treasury path, bridge or production payment rail exists.

Every adapter requires an exact network identity, asset identity, testnet canary, validation rules, finality policy, quote expiry, fee handling, refund design, secret scan, independent review and owner production gate.

## Settlement

8x8 may accept native BTC and XMR while preferring explicitly allowlisted stablecoin routes on supported smart-contract networks.

Rules:

- network and asset contract or mint must be verified;
- bridged and wrapped assets are not silently treated as native assets;
- no automatic swap or bridge in V1;
- quote, fees and maximum slippage must be shown before a future conversion;
- every conversion remains an exact-gated financial action;
- underpaid, overpaid, expired, failed and refund-review states remain auditable.

## Agent policy accounts

Agents do not independently own legal assets or wallets.

An agent wallet means an owner-controlled policy account assigned to an agent identity for receiving, accounting, budgeting, simulation or proposal generation.

Defaults:

- watch-only, receive-only or internal-ledger-only;
- no seed or private key exposed to an agent;
- no autonomous spend, withdrawal, swap or bridge;
- exact owner or multisig gate for every financial action;
- destination allowlists, daily limits, receipts and immediate revocation.

## Public connector

The 8x8 connector is designed for CLI, SDK, MCP, ChatGPT-app style integration, web, mobile and API clients.

Default public scopes may include profile, entitlement, usage, tasks, artifacts, worlds, maps, simulations and receipts.

Wallet signing, spending, swapping, bridging and private-owner controls are never default public scopes.

## Platform surfaces

The shared product-surface contract covers:

- private web command deck
- public web and PWA
- Android
- iOS
- CLI and SDK
- MCP and ChatGPT connector
- Telegram Mini App
- VR environment
- Vectras node
- ROM shell

Every surface must report its audience, authority, data classes, capabilities, entitlement rule, deployment truth and evidence.

## Production gates

Production remains blocked until the relevant surface has:

- security and privacy review;
- legal, tax and payment review where applicable;
- verified entitlement and anti-abuse tests;
- payment-state and confirmation tests;
- wallet no-secret/no-autonomous-spend tests;
- accessibility and mobile tests;
- rollback;
- current CI;
- preview or testnet receipts;
- exact owner approval.
