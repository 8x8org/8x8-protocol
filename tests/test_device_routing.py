from __future__ import annotations

import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_device_routing.py"
SPEC = importlib.util.spec_from_file_location("validate_device_routing", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

CAPABILITY = json.loads(
    (ROOT / "examples/device-capability.remote-asic.simulated.json").read_text(encoding="utf-8")
)
ALLOCATION = json.loads(
    (ROOT / "examples/work-allocation.remote-asic-btc.simulated.json").read_text(encoding="utf-8")
)
SETTLEMENT = json.loads(
    (ROOT / "examples/treasury-settlement.simulated.json").read_text(encoding="utf-8")
)


class DeviceRoutingTests(unittest.TestCase):
    def test_repository_contract_passes(self) -> None:
        self.assertEqual(MODULE.validate(ROOT), [])

    def test_mobile_pow_is_rejected(self) -> None:
        capability = deepcopy(CAPABILITY)
        capability["platform"] = "GOOGLE_PLAY"
        failures = MODULE.validate_allocation(capability, deepcopy(ALLOCATION))
        self.assertTrue(any("GOOGLE_PLAY" in x for x in failures))

    def test_ethereum_pow_is_rejected(self) -> None:
        allocation = deepcopy(ALLOCATION)
        allocation["network_or_domain"] = "ETHEREUM_MAINNET"
        failures = MODULE.validate_allocation(deepcopy(CAPABILITY), allocation)
        self.assertTrue(any("Ethereum Mainnet" in x for x in failures))

    def test_bitcoin_requires_asic_and_sha256(self) -> None:
        capability = deepcopy(CAPABILITY)
        capability["hardware_class"] = "GENERAL_CPU"
        allocation = deepcopy(ALLOCATION)
        allocation["algorithm_or_protocol"] = "RANDOMX"
        failures = MODULE.validate_allocation(capability, allocation)
        self.assertTrue(any("ASIC_MINER" in x for x in failures))

    def test_standard_profile_cannot_exceed_25_percent(self) -> None:
        allocation = deepcopy(ALLOCATION)
        allocation["resource_ceiling"]["available_memory_percent"] = 26
        failures = MODULE.validate_allocation(deepcopy(CAPABILITY), allocation)
        self.assertTrue(any("STANDARD_25" in x for x in failures))

    def test_settlement_must_reconcile(self) -> None:
        settlement = deepcopy(SETTLEMENT)
        settlement["user_reward_pool"] += 1
        failures = MODULE.validate_settlement(settlement)
        self.assertTrue(any("reconcile" in x for x in failures))

    def test_fee_amount_is_checked(self) -> None:
        settlement = deepcopy(SETTLEMENT)
        settlement["ecosystem_fee_amount"] += 1
        failures = MODULE.validate_settlement(settlement)
        self.assertTrue(any("fee mismatch" in x for x in failures))


if __name__ == "__main__":
    unittest.main()
