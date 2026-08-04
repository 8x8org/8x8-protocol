# 8x8 Private Code / Public Service Boundary V1

## Product rule

8x8 may be publicly usable without publishing the private control plane, private agent prompts, credentials, provider routing, internal memories, owner workspaces, private source repositories, operational receipts containing sensitive topology, or wallet authority.

The public product exposes **capabilities through contracts**, not the private implementation itself.

## Publicly exposable

- public web and PWA clients;
- mobile clients distributed through approved stores;
- CLI and SDK packages that call documented APIs;
- MCP or ChatGPT-app tools with least-authority scopes;
- Telegram Mini App and approved Discord connector surfaces;
- public schemas, conformance fixtures and receipt verifiers;
- user profile, entitlement, usage and billing interfaces;
- public-safe agent identities and capability descriptions;
- sanitized world, map, simulation and content artifacts;
- status pages backed by public-safe health contracts;
- API documentation, examples and rate-limit behavior.

## Private-only

- owner authority and exact-gate material;
- service-control or arbitrary-shell capability;
- credentials, signing keys, seeds, private wallet descriptors and spend authority;
- private memory, messages, email, legal documents and unrestricted logs;
- private provider keys, routing policy and model credentials;
- private agent prompts, hidden evaluation data and proprietary orchestration logic;
- internal security findings and unredacted dependency topology;
- source code designated proprietary or trade-secret;
- private databases and control-fabric state.

## Required architecture

```text
Public Client
  -> Public API Gateway
  -> Identity + Entitlement
  -> Capability Broker
  -> Sanitized Task Contract
  -> Private Execution Adapter
  -> Policy / Authority Gate
  -> Agent or Tool Runtime
  -> Redaction + Receipt
  -> Public Result
```

The public gateway must never mount private repositories, credential directories or owner workspaces. Private execution adapters must accept only typed, bounded tasks and return typed, sanitized results.

## User identity

Every user receives a stable `8X8-*` profile ID after account creation. Public handles and display names are distinct from legal names. Legal names are private by default. Email verification, password or passkey protection, recovery, rate limiting, session revocation and audit receipts are required before paid activation.

Passwords must be stored only through a modern password-hashing system. Plaintext, reversible encryption and client-side trust are forbidden. The protocol does not prescribe a vendor, but production implementation must document parameters, rotation and breach response.

## Entitlement

- Trial: 5,280 server-metered seconds.
- Paid unit price: USD 8.88 per month.
- Supported billing terms: 1, 3, 6, 9 and 12 months.
- Prepaid totals are exact multiples unless a separately approved discount policy changes them.
- Usage, trial exhaustion, payment and renewal decisions are server-authoritative.
- Client clocks and local storage are not entitlement authority.

## Models and agents

The private estate may route across hundreds of models and agents, but public users receive capability-based service levels rather than unrestricted access to every internal identity or provider.

A model registry entry proves only the recorded evidence state. An agent profile or SOUL file is not proof of a live worker. Productive claims require task identity, runtime evidence and a receipt.

## Discord and communication surfaces

Discord, Telegram and other communication connectors are optional client surfaces. They must use explicit guild/channel/topic allowlists, redact stored content, separate drafts from sends, and require exact gates for public posts, DMs, moderation or external publication.

## Wallet and payment boundary

The public application may create payment intents and display receive-only invoices. It must not contain private keys or autonomous spend authority. Bitcoin and Monero wallets confirmed by the owner remain private and uninspected. Agent wallet identities are owner-controlled policy accounts, not independent legal owners.

## Release gates

Production publication requires all of:

1. threat model and security review;
2. privacy and retention review;
3. identity and account-recovery tests;
4. entitlement and anti-abuse tests;
5. payment, refund, tax and sanctions review;
6. secret scan and private-boundary tests;
7. accessibility and mobile review;
8. rate-limit and denial-of-service tests;
9. receipt and audit verification;
10. rollback and incident-response rehearsal;
11. explicit owner release approval.

Source presence, a preview URL or a green screenshot is not production approval.
