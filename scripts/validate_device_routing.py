#!/usr/bin/env python3
"""Validate device routing, mining eligibility, and treasury settlement invariants."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCHEMAS = (
    "schemas/device-capability.schema.json",
    "schemas/work-allocation.schema.json",
    "schemas/treasury-settlement.schema.json",
)
EXAMPLES = (
    "examples/device-capability.remote-asic.simulated.json",
    "examples/work-allocation.remote-asic-btc.simulated.json",
    "examples/treasury-settlement.simulated.json",
)


def load(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain an object")
    return value


def validate_allocation(capability: dict[str, Any], allocation: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    platform = capability.get("platform")
    hardware = capability.get("hardware_class")
    roles = set(capability.get("roles", []))
    workload = allocation.get("workload_type")
    network = str(allocation.get("network_or_domain", "")).upper()
    algorithm = str(allocation.get("algorithm_or_protocol", "")).upper()
    profile = allocation.get("profile_id")
    ceiling = allocation.get("resource_ceiling", {})

    if allocation.get("node_id") != capability.get("node_id"):
        failures.append("allocation node does not match capability node")
    if allocation.get("capability_attestation_id") != capability.get("attestation_id"):
        failures.append("allocation does not reference the capability attestation")
    if allocation.get("profitability_guaranteed") is not False:
        failures.append("profitability cannot be guaranteed")

    if profile == "STANDARD_25":
        for key in ("cpu_percent", "gpu_percent", "available_memory_percent"):
            if float(ceiling.get(key, 0)) > 25:
                failures.append(f"STANDARD_25 exceeds 25% for {key}")
    if profile == "ENHANCED_75":
        for key in ("cpu_percent", "gpu_percent", "available_memory_percent"):
            if float(ceiling.get(key, 0)) > 75:
                failures.append(f"ENHANCED_75 exceeds 75% for {key}")

    if workload == "POW_MINING":
        if platform in {"APPLE_APP_STORE", "GOOGLE_PLAY", "TELEGRAM_MINI_APP", "BROWSER"}:
            failures.append(f"{platform} cannot receive local POW_MINING work")
        if capability.get("local_crypto_mining_policy") not in {
            "ELIGIBILITY_GATED",
            "SUPPORTED_AFTER_ALLOWLISTING",
        }:
            failures.append("capability policy does not allow proof-of-work mining")
        if "MINING_ELIGIBLE" not in roles:
            failures.append("proof-of-work allocation requires MINING_ELIGIBLE role")
        if allocation.get("treasury_destination_ref") is None:
            failures.append("proof-of-work allocation requires treasury destination")
        if "ETHEREUM" in network or network in {"ETH", "ETH_MAINNET"}:
            failures.append("Ethereum Mainnet cannot receive proof-of-work allocation")
        if "BITCOIN" in network or network == "BTC":
            if hardware != "ASIC_MINER" or algorithm != "SHA-256":
                failures.append("Bitcoin allocation requires ASIC_MINER and SHA-256")

    if workload == "POS_VALIDATION" and allocation.get("treasury_destination_ref") is None:
        failures.append("validation allocation requires treasury destination")

    return failures


def validate_settlement(settlement: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    deductions = settlement.get("deductions", {})
    deduction_total = sum(int(value) for value in deductions.values())
    gross = int(settlement.get("gross_proceeds", 0))
    fee_bps = int(settlement.get("ecosystem_fee_bps", 0))
    fee_amount = int(settlement.get("ecosystem_fee_amount", 0))
    fee_base = gross - deduction_total
    expected_fee = max(fee_base, 0) * fee_bps // 10000
    if fee_amount != expected_fee:
        failures.append(
            f"ecosystem fee mismatch: expected {expected_fee}, received {fee_amount}"
        )

    outputs = (
        fee_amount
        + int(settlement.get("user_reward_pool", 0))
        + int(settlement.get("treasury_reserve", 0))
        + int(settlement.get("pending_dispute_reserve", 0))
        + int(settlement.get("rounding_remainder", 0))
    )
    if gross != deduction_total + outputs:
        failures.append("treasury settlement does not reconcile exactly")
    if settlement.get("reconciles") is not True:
        failures.append("reconciles must be true")
    if settlement.get("stage") == "SIMULATED":
        if settlement.get("transaction_reference") is not None:
            failures.append("simulated settlement cannot contain transaction reference")
        if settlement.get("finalized_at") is not None:
            failures.append("simulated settlement cannot contain finalized_at")
    return failures


def validate(root: Path) -> list[str]:
    failures: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    required = (*SCHEMAS, *EXAMPLES, "specs/device-work-routing-and-treasury-v0.1.md")
    for relative in required:
        if not (root / relative).is_file():
            failures.append(f"missing required file: {relative}")
            continue
        if relative.endswith(".json"):
            try:
                loaded[relative] = load(root, relative)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                failures.append(f"invalid JSON {relative}: {exc}")
    if failures:
        return failures

    for relative in SCHEMAS:
        if loaded[relative].get("additionalProperties") is not False:
            failures.append(f"{relative} must reject unknown top-level fields")

    capability = loaded[EXAMPLES[0]]
    allocation = loaded[EXAMPLES[1]]
    settlement = loaded[EXAMPLES[2]]

    if capability.get("hardware_class") != "ASIC_MINER":
        failures.append("public routing fixture must remain ASIC_MINER")
    if capability.get("platform") != "REMOTE_ASIC_RIG":
        failures.append("public routing fixture must remain REMOTE_ASIC_RIG")
    if capability.get("local_crypto_mining_policy") != "SUPPORTED_AFTER_ALLOWLISTING":
        failures.append("remote ASIC fixture must require allowlisting")

    failures.extend(validate_allocation(capability, allocation))
    failures.extend(validate_settlement(settlement))

    if allocation.get("reward_accounting_stage") != "SIMULATED":
        failures.append("public allocation fixture must remain simulated")
    if settlement.get("stage") != "SIMULATED":
        failures.append("public settlement fixture must remain simulated")

    spec = (root / "specs/device-work-routing-and-treasury-v0.1.md").read_text(
        encoding="utf-8"
    )
    for text in (
        "DESIGN DRAFT — NOT RELEASED",
        "Apple App Store and Google Play clients cannot perform local cryptocurrency mining",
        "Ethereum Mainnet is not eligible for `POW_MINING`",
        "nine utility symbols against an intended eight-token model",
    ):
        if text not in spec:
            failures.append(f"routing specification missing: {text}")

    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures = validate(root)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("DEVICE_ROUTING_AND_TREASURY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
