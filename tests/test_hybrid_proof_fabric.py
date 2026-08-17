from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_hybrid_proof_fabric.py"
SPEC = importlib.util.spec_from_file_location("hybrid_proofs", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HybridProofTests(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for relative in (
            "specs/hybrid-proof-fabric-v0.1.md",
            "registries/proof-suite.v0.1.json",
            "schemas/proof-receipt.schema.json",
            "schemas/seraphim-reputation-proof.schema.json",
            "examples/proof-receipt.service.simulated.json",
            "examples/seraphim-reputation-proof.simulated.json",
        ):
            source = ROOT / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        return temporary, root

    def test_repository_contract_passes(self) -> None:
        self.assertEqual(MODULE.validate(ROOT), [])

    def test_useful_work_cannot_be_promoted_without_verification(self) -> None:
        temporary, root = self.fixture()
        self.addCleanup(temporary.cleanup)
        path = root / "registries/proof-suite.v0.1.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        for row in doc["proofs"]:
            if row["proof_type"] == "PROOF_OF_USEFUL_WORK":
                row["maturity"] = "IMPLEMENTED"
                row["reward_eligible"] = True
        path.write_text(json.dumps(doc), encoding="utf-8")
        self.assertTrue(any("Useful Work" in x for x in MODULE.validate(root)))

    def test_reputation_cannot_equal_authorization(self) -> None:
        temporary, root = self.fixture()
        self.addCleanup(temporary.cleanup)
        path = root / "registries/proof-suite.v0.1.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["forbidden_equivalences"].remove("REPUTATION_EQUALS_AUTHORIZATION")
        path.write_text(json.dumps(doc), encoding="utf-8")
        self.assertTrue(any("forbidden-equivalence" in x for x in MODULE.validate(root)))

    def test_srp_cannot_become_transferable(self) -> None:
        temporary, root = self.fixture()
        self.addCleanup(temporary.cleanup)
        path = root / "examples/seraphim-reputation-proof.simulated.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["transferable"] = True
        path.write_text(json.dumps(doc), encoding="utf-8")
        self.assertTrue(any("transferable" in x for x in MODULE.validate(root)))

    def test_srp_cannot_gain_financial_authority(self) -> None:
        temporary, root = self.fixture()
        self.addCleanup(temporary.cleanup)
        path = root / "examples/seraphim-reputation-proof.simulated.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["financial_authority"] = True
        path.write_text(json.dumps(doc), encoding="utf-8")
        self.assertTrue(any("financial_authority" in x for x in MODULE.validate(root)))

    def test_poa_cannot_become_production_target(self) -> None:
        temporary, root = self.fixture()
        self.addCleanup(temporary.cleanup)
        path = root / "registries/proof-suite.v0.1.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["consensus_target"]["production"] = "PROOF_OF_AUTHORITY"
        path.write_text(json.dumps(doc), encoding="utf-8")
        self.assertTrue(any("PoS+BFT" in x for x in MODULE.validate(root)))


if __name__ == "__main__":
    unittest.main()
