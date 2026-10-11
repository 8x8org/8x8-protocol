#!/usr/bin/env python3
"""Validate the 8x8 hybrid proof registry and Seraphim credential boundaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_PROOFS = {
    "PROOF_OF_STAKE_BFT": "CONSENSUS",
    "BITCOIN_POW_CHECKPOINT": "ANCHORING",
    "PROOF_OF_AUTHORITY": "CONSENSUS_DEV_ONLY",
    "PROOF_OF_COMPUTE": "CONTRIBUTION",
    "PROOF_OF_USEFUL_WORK": "CONTRIBUTION_RESEARCH",
    "PROOF_OF_REPLICATION": "STORAGE",
    "PROOF_OF_SPACETIME": "STORAGE",
    "PROOF_OF_AVAILABILITY": "STORAGE_AND_DATA",
    "PROOF_OF_SERVICE": "SERVICE",
    "PROOF_OF_KNOWLEDGE": "CREDENTIAL_OR_ZK",
    "PROOF_OF_CONTRIBUTION": "AGGREGATION",
    "PROOF_OF_REPUTATION": "REPUTATION",
    "PROOF_OF_TIME_ORDERING": "ORDERING_SUPPORT",
    "PROOF_OF_DEVICE_ATTESTATION": "IDENTITY_AND_RUNTIME",
    "PROOF_OF_AGENT_IDENTITY": "IDENTITY_AND_RUNTIME",
    "PROOF_OF_AUTHORIZATION": "AUTHORITY",
}


def load(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain an object")
    return value


def validate(root: Path) -> list[str]:
    failures: list[str] = []
    required = (
        "specs/hybrid-proof-fabric-v0.1.md",
        "registries/proof-suite.v0.1.json",
        "schemas/proof-receipt.schema.json",
        "schemas/seraphim-reputation-proof.schema.json",
        "examples/proof-receipt.service.simulated.json",
        "examples/seraphim-reputation-proof.simulated.json",
    )
    loaded: dict[str, dict[str, Any]] = {}
    for relative in required:
        path = root / relative
        if not path.is_file():
            failures.append(f"missing required file: {relative}")
        elif relative.endswith(".json"):
            try:
                loaded[relative] = load(root, relative)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                failures.append(f"invalid JSON {relative}: {exc}")
    if failures:
        return failures

    registry = loaded["registries/proof-suite.v0.1.json"]
    if registry.get("schema") != "8x8.proof-suite-registry.v0.1":
        failures.append("unexpected proof registry schema")
    if registry.get("status") != "DESIGN_NOT_RELEASED":
        failures.append("proof registry must remain design-only")
    consensus = registry.get("consensus_target", {})
    if consensus.get("production") != "PROOF_OF_STAKE_BFT":
        failures.append("production consensus target must remain PoS+BFT")
    if consensus.get("external_anchor") != "BITCOIN_POW_CHECKPOINT_RESEARCH":
        failures.append("Bitcoin PoW anchoring must remain research-gated")
    if consensus.get("development_only") != "PROOF_OF_AUTHORITY":
        failures.append("PoA must remain development-only")

    rows = registry.get("proofs", [])
    observed = {row.get("proof_type"): row.get("proof_class") for row in rows}
    if observed != EXPECTED_PROOFS:
        failures.append("canonical proof types or classes changed")
    for row in rows:
        if row.get("verifier_required") is not True:
            failures.append(f"{row.get('proof_type')} requires a verifier")
        if row.get("proof_type") == "PROOF_OF_USEFUL_WORK":
            if row.get("maturity") != "RESEARCH_ONLY" or row.get("reward_eligible") is not False:
                failures.append("Proof of Useful Work must remain research-only and not reward eligible")
        if row.get("proof_type") in {"PROOF_OF_REPUTATION", "PROOF_OF_KNOWLEDGE", "PROOF_OF_AUTHORIZATION"}:
            if row.get("reward_eligible") is not False:
                failures.append(f"{row.get('proof_type')} cannot directly create rewards")

    forbidden = set(registry.get("forbidden_equivalences", []))
    required_forbidden = {
        "CONTRIBUTION_PROOF_EQUALS_CONSENSUS",
        "REPUTATION_EQUALS_AUTHORIZATION",
        "AUTHORIZATION_EQUALS_EXECUTION",
        "COMPUTATION_EQUALS_USEFUL_WORK",
        "ACTIVITY_COUNT_EQUALS_REWARD",
        "AI_OUTPUT_EQUALS_KNOWLEDGE_PROOF",
    }
    if forbidden != required_forbidden:
        failures.append("proof forbidden-equivalence set changed")

    proof_schema = loaded["schemas/proof-receipt.schema.json"]
    srp_schema = loaded["schemas/seraphim-reputation-proof.schema.json"]
    if proof_schema.get("additionalProperties") is not False:
        failures.append("proof receipt schema must reject unknown fields")
    if srp_schema.get("additionalProperties") is not False:
        failures.append("SRP schema must reject unknown fields")
    srp_properties = srp_schema.get("properties", {})
    for key in ("transferable", "saleable", "swappable", "authority_expansion_allowed", "financial_authority"):
        if srp_properties.get(key, {}).get("const") is not False:
            failures.append(f"SRP schema {key} must be false")
    if srp_properties.get("revocable", {}).get("const") is not True:
        failures.append("SRP schema must require revocation support")

    proof = loaded["examples/proof-receipt.service.simulated.json"]
    if proof.get("proof_type") != "PROOF_OF_SERVICE" or proof.get("proof_class") != "SERVICE":
        failures.append("service proof fixture identity changed")
    if proof.get("reward_eligibility") != "SIMULATED":
        failures.append("public service proof fixture must remain simulated")
    if proof.get("verification_result") != "PASS":
        failures.append("service proof fixture must remain a passing simulated canary")

    srp = loaded["examples/seraphim-reputation-proof.simulated.json"]
    for key in ("transferable", "saleable", "swappable", "authority_expansion_allowed", "financial_authority"):
        if srp.get(key) is not False:
            failures.append(f"SRP fixture {key} must remain false")
    if srp.get("revocable") is not True:
        failures.append("SRP fixture must remain revocable")
    if srp.get("revocation_state") != "ACTIVE":
        failures.append("SRP fixture must remain active simulated evidence")

    spec = (root / "specs/hybrid-proof-fabric-v0.1.md").read_text(encoding="utf-8")
    for text in (
        "Consensus and finality plane",
        "Contribution and service plane",
        "Proof of Useful Work",
        "Proof of Knowledge is a cryptographic or credential-based assertion",
        "Neither identity may expand its own authority",
    ):
        if text not in spec:
            failures.append(f"hybrid proof specification missing: {text}")

    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures = validate(root)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("HYBRID_PROOF_FABRIC=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
