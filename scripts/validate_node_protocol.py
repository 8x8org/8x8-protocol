#!/usr/bin/env python3
"""Validate hard safety invariants for the public node protocol draft."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_FILES = (
    "schemas/node-consent.schema.json",
    "schemas/resource-receipt.schema.json",
    "schemas/reward-event.schema.json",
)
FIXTURE_FILES = (
    "examples/node-consent.simulated.json",
    "examples/resource-receipt.simulated.json",
    "examples/reward-event.simulated.json",
)
FORBIDDEN_PROPERTY_NAMES = {
    "api_key",
    "api_keys",
    "password",
    "private_key",
    "wallet_private_key",
    "secret_value",
    "cookie_value",
    "access_token",
    "refresh_token",
}


def load(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain a JSON object")
    return value


def property_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        names.update(str(key).lower() for key in value)
        for child in value.values():
            names.update(property_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(property_names(child))
    return names


def validate(root: Path) -> list[str]:
    failures: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}

    for relative in (*SCHEMA_FILES, *FIXTURE_FILES):
        path = root / relative
        if not path.is_file():
            failures.append(f"missing required file: {relative}")
            continue
        try:
            loaded[relative] = load(root, relative)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            failures.append(f"invalid JSON {relative}: {exc}")

    if failures:
        return failures

    consent_schema = loaded[SCHEMA_FILES[0]]
    receipt_schema = loaded[SCHEMA_FILES[1]]
    reward_schema = loaded[SCHEMA_FILES[2]]
    consent = loaded[FIXTURE_FILES[0]]
    receipt = loaded[FIXTURE_FILES[1]]
    reward = loaded[FIXTURE_FILES[2]]

    if consent_schema.get("additionalProperties") is not False:
        failures.append("node consent schema must deny unknown top-level fields")
    if receipt_schema.get("additionalProperties") is not False:
        failures.append("resource receipt schema must deny unknown top-level fields")
    if reward_schema.get("additionalProperties") is not False:
        failures.append("reward event schema must deny unknown top-level fields")

    consent_properties = consent_schema["properties"]
    if consent_properties["local_pause_required"].get("const") is not True:
        failures.append("local pause must be required")
    if consent_properties["kill_switch_required"].get("const") is not True:
        failures.append("kill switch must be required")

    resource_classes = set(consent_properties["resource_class"]["enum"])
    expected_classes = {
        "CPU",
        "GPU",
        "STORAGE",
        "BANDWIDTH",
        "TELEMETRY",
        "REMOTE_MINER_MANAGEMENT",
        "PRECISE_LOCATION",
        "REWARDS",
    }
    if resource_classes != expected_classes:
        failures.append("resource classes must remain explicit and complete")

    reward_properties = reward_schema["properties"]
    if reward_properties["guaranteed_value"].get("const") is not False:
        failures.append("reward events must forbid guaranteed value claims")
    if reward_properties["investment_claim"].get("const") is not False:
        failures.append("reward events must forbid investment claims")

    names = set()
    for relative in SCHEMA_FILES:
        names.update(property_names(loaded[relative]))
    exposed = sorted(names & FORBIDDEN_PROPERTY_NAMES)
    if exposed:
        failures.append(f"schemas expose secret-value properties: {exposed}")

    if consent.get("reward_participation") != "SIMULATED":
        failures.append("public consent fixture must remain simulated")
    if consent.get("secret_reference_ids") != []:
        failures.append("public consent fixture must contain no secret references")
    if consent.get("local_pause_required") is not True:
        failures.append("fixture must require local pause")
    if consent.get("kill_switch_required") is not True:
        failures.append("fixture must require kill switch")

    if receipt.get("reward_stage") != "SIMULATED":
        failures.append("public receipt fixture must remain simulated")
    if receipt.get("transaction_reference") is not None:
        failures.append("simulated receipt cannot contain a transaction reference")
    privacy = receipt.get("privacy_assertions", {})
    if not privacy or not all(value is True for value in privacy.values()):
        failures.append("all receipt privacy assertions must be true")

    if reward.get("stage") != "SIMULATED":
        failures.append("public reward fixture must remain simulated")
    if reward.get("quantity") != 0:
        failures.append("public reward fixture quantity must remain zero")
    if reward.get("asset_reference") is not None:
        failures.append("simulated reward cannot reference an asset")
    if reward.get("transaction_reference") is not None:
        failures.append("simulated reward cannot reference a transaction")
    if reward.get("guaranteed_value") is not False:
        failures.append("fixture cannot claim guaranteed value")
    if reward.get("investment_claim") is not False:
        failures.append("fixture cannot make an investment claim")

    spec = (root / "specs/node-contribution-v0.1.md").read_text(encoding="utf-8")
    for required_text in (
        "DESIGN DRAFT — NOT RELEASED",
        "must not mine cryptocurrency on the mobile device",
        "Precise location is not a default node resource",
        "opaque secret references only",
    ):
        if required_text not in spec:
            failures.append(f"protocol specification missing: {required_text}")

    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures = validate(root)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("NODE_PROTOCOL_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
