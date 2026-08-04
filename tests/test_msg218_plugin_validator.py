from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_8x8_plugin import PluginValidationError, validate_plugin

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/plugins/8x8-plugin-manifest-v1.schema.json").read_text())
MANIFEST = json.loads((ROOT / "examples/plugins/public-status-card/8x8-plugin.json").read_text())


class PluginValidatorTests(unittest.TestCase):
    def test_example_plugin_is_catalog_review_eligible(self):
        receipt = validate_plugin(copy.deepcopy(MANIFEST), SCHEMA)
        self.assertEqual(receipt["plugin_id"], "community.public-status-card")
        self.assertEqual(receipt["conformance_score"], 100)
        self.assertEqual(receipt["default_permission"], "DENY")
        self.assertEqual(receipt["financial_authority"], "NONE")
        self.assertTrue(receipt["rollback_tested"])
        self.assertTrue(receipt["eligible_for_catalog_review"])
        self.assertEqual(receipt["external_actions"], 0)

    def test_validator_is_deterministic(self):
        first = validate_plugin(copy.deepcopy(MANIFEST), SCHEMA)
        second = validate_plugin(copy.deepcopy(MANIFEST), SCHEMA)
        self.assertEqual(first, second)

    def test_financial_authority_is_rejected_by_schema(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest["permissions"]["financial"] = "TRADE"
        with self.assertRaises(PluginValidationError):
            validate_plugin(manifest, SCHEMA)

    def test_score_100_requires_security_and_rollback_tests(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest["tests"]["security"] = False
        with self.assertRaises(PluginValidationError):
            validate_plugin(manifest, SCHEMA)
        manifest = copy.deepcopy(MANIFEST)
        manifest["rollback"]["tested"] = False
        with self.assertRaises(PluginValidationError):
            validate_plugin(manifest, SCHEMA)

    def test_unknown_permission_field_is_rejected(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest["permissions"]["unrestricted_shell"] = True
        with self.assertRaises(PluginValidationError):
            validate_plugin(manifest, SCHEMA)


if __name__ == "__main__":
    unittest.main()
