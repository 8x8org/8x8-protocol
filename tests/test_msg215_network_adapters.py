#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "msg215_network_adapter_cases.json"
DATA = json.loads(FIXTURE.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_unique_evidence_backed_adapters() -> None:
    adapters = DATA["positive"]
    adapter_ids = [item["adapter_id"] for item in adapters]
    require(len(adapter_ids) == len(set(adapter_ids)), "network adapters require unique IDs")
    for adapter in adapters:
        require(adapter["evidence"], f"{adapter['adapter_id']} requires evidence")
        require(adapter["secret_material_present"] is False, "adapter cannot contain secret material")
        require(adapter["spend_authority_present"] is False, "adapter cannot contain spend authority")
        require(adapter["live_actions_enabled"] is False, "adapter fixtures cannot enable live actions")
        require(adapter["automatic_swap_enabled"] is False, "automatic swaps remain disabled")
        require(adapter["automatic_bridge_enabled"] is False, "automatic bridges remain disabled")


def test_network_identity_and_mode() -> None:
    for adapter in DATA["positive"]:
        network = adapter["network"]
        namespace = adapter["namespace"]
        mode = adapter["mode"]
        if network == "BITCOIN":
            require(namespace == "BIP122", "Bitcoin requires BIP122 network identity")
            require(mode in {"WATCH_ONLY", "RECEIVE_ONLY", "SIMULATED"}, "Bitcoin must remain watch/receive only")
        elif network == "MONERO":
            require(namespace == "MONERO_NETWORK", "Monero requires explicit Monero network identity")
            require(mode in {"VIEW_ONLY", "RECEIVE_ONLY", "SIMULATED"}, "Monero must remain view/receive only")
        elif network in {"ETHEREUM", "BNB_SMART_CHAIN", "SOLANA"}:
            require(namespace == "CAIP2", f"{network} requires CAIP-2 identity")
        elif network == "TON":
            require(namespace == "TON_NETWORK", "TON requires explicit TON network identity")
        elif network == "PI_NETWORK":
            require(namespace == "PI_NETWORK", "Pi requires explicit Pi network identity")
            require(adapter["environment"] == "SANDBOX", "Pi fixture must remain sandbox-only")
            require(mode == "SIMULATED", "Pi fixture must remain simulated")


def test_finality_is_explicit() -> None:
    for adapter in DATA["positive"]:
        require(adapter["confirmation_basis"] in {"BLOCK_CONFIRMATIONS", "FINALIZED_CHECKPOINT", "NETWORK_ACCEPTED", "SIMULATED"}, "unknown finality basis")
        require(isinstance(adapter["minimum_confirmations"], int) and adapter["minimum_confirmations"] >= 0, "invalid confirmation count")
        require(adapter["reorg_handling"] in {"REVOKE_PENDING", "RECHECK_UNTIL_FINAL", "NOT_APPLICABLE"}, "reorg policy required")


def test_negative_cases_remain_rejected() -> None:
    cases = {item["case"]: item for item in DATA["negative"]}
    require(cases["bitcoin_wrong_namespace"]["namespace"] != "BIP122", "Bitcoin wrong-namespace fixture must be unsafe")
    require(cases["monero_wrong_mode"]["mode"] not in {"VIEW_ONLY", "RECEIVE_ONLY", "SIMULATED"}, "Monero wrong-mode fixture must be unsafe")
    require(cases["secret_material_present"]["secret_material_present"] is True, "secret fixture must be unsafe")
    require(cases["spend_authority_present"]["spend_authority_present"] is True, "spend-authority fixture must be unsafe")
    require(cases["live_actions_enabled"]["live_actions_enabled"] is True, "live-action fixture must be unsafe")
    require(cases["automatic_swap_enabled"]["automatic_swap_enabled"] is True, "swap fixture must be unsafe")
    require(cases["automatic_bridge_enabled"]["automatic_bridge_enabled"] is True, "bridge fixture must be unsafe")
    duplicate_ids = cases["duplicate_adapter_ids"]["adapter_ids"]
    require(len(set(duplicate_ids)) < len(duplicate_ids), "duplicate adapter fixture must be rejected")


def main() -> None:
    tests = [
        test_unique_evidence_backed_adapters,
        test_network_identity_and_mode,
        test_finality_is_explicit,
        test_negative_cases_remain_rejected,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS total={len(tests)} fixture={FIXTURE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
