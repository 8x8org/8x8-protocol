from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/msg218_progressive_release_cases.json"
SCHEMAS = {
    "release_unit": ROOT / "schemas/release/8x8-release-unit-v1.schema.json",
    "plugin": ROOT / "schemas/plugins/8x8-plugin-manifest-v1.schema.json",
    "hidden_presence": ROOT / "schemas/presence/8x8-presence-privacy-v1.schema.json",
    "world_node": ROOT / "schemas/world/8x8-world-node-v1.schema.json",
}


class ProgressiveReleaseContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.validators = {
            name: Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))
            for name, path in SCHEMAS.items()
        }

    def assert_valid(self, name, value):
        errors = sorted(self.validators[name].iter_errors(value), key=lambda error: list(error.path))
        self.assertEqual([], [error.message for error in errors])

    def assert_invalid(self, name, value):
        self.assertTrue(list(self.validators[name].iter_errors(value)))

    def test_all_positive_fixtures_validate(self):
        for name, value in self.fixture.items():
            self.assert_valid(name, value)

    def test_release_eligible_requires_full_score(self):
        value = copy.deepcopy(self.fixture["release_unit"])
        value["score"]["earned"] = 99
        self.assert_invalid("release_unit", value)

    def test_release_eligible_requires_every_gate(self):
        for gate in self.fixture["release_unit"]["gates"]:
            value = copy.deepcopy(self.fixture["release_unit"])
            value["gates"][gate] = False
            self.assert_invalid("release_unit", value)

    def test_deployed_requires_receipt_and_timestamp(self):
        value = copy.deepcopy(self.fixture["release_unit"])
        value["truth_state"] = "DEPLOYED"
        self.assert_invalid("release_unit", value)
        value["released_at"] = "2026-08-04T19:30:00Z"
        value["release_receipt_id"] = "receipt:deployment:1"
        self.assert_valid("release_unit", value)

    def test_plugin_defaults_to_deny_and_has_no_financial_scope(self):
        value = self.fixture["plugin"]
        self.assertEqual(value["permissions"]["default"], "DENY")
        self.assertEqual(value["permissions"]["financial"], "NONE")
        self.assertEqual(value["permissions"]["network"], [])
        self.assert_valid("plugin", value)

    def test_plugin_score_100_requires_all_tests_and_rollback(self):
        value = copy.deepcopy(self.fixture["plugin"])
        value["tests"]["security"] = False
        self.assert_invalid("plugin", value)
        value = copy.deepcopy(self.fixture["plugin"])
        value["rollback"]["tested"] = False
        self.assert_invalid("plugin", value)

    def test_no_consent_forces_hidden_presence(self):
        value = copy.deepcopy(self.fixture["hidden_presence"])
        value["visibility"] = "COUNTRY"
        value["location"]["country_code"] = "US"
        value["location"]["source"] = "USER_SELECTED"
        self.assert_invalid("hidden_presence", value)

    def test_approximate_visibility_cannot_include_coordinates(self):
        value = copy.deepcopy(self.fixture["hidden_presence"])
        value["consent"]["granted"] = True
        value["consent"]["granted_at"] = "2026-08-04T19:30:00Z"
        value["visibility"] = "CITY_APPROXIMATE"
        value["location"].update({
            "country_code": "FR",
            "region_code": "IDF",
            "city_label": "Paris area",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "precision_meters": 10000,
            "source": "DEVICE_APPROXIMATE",
        })
        self.assert_invalid("hidden_presence", value)

    def test_world_health_color_semantics_are_enforced(self):
        value = copy.deepcopy(self.fixture["world_node"])
        value["status"]["color_token"] = "RED"
        self.assert_invalid("world_node", value)


if __name__ == "__main__":
    unittest.main()
