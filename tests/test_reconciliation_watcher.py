import unittest
from datetime import datetime, timezone

from runtime_integration.reconciliation_watcher import reconcile


NOW = datetime(2026, 8, 6, 13, 5, tzinfo=timezone.utc)


class ReconciliationWatcherTests(unittest.TestCase):
    def base(self):
        return {
            "product_version": "0.0.1",
            "sources": [{
                "source_id": "github-health-receipt",
                "observed_at": "2026-08-06T13:04:00Z",
                "freshness_seconds": 3600,
                "evidence_state": "OBSERVED",
                "reality": "PRIVATE_PAST",
                "summary": "Sanitized health receipt published"
            }],
            "active_writers": [],
            "claude_runtime_visibility": "REPORTED_ACTIVE_NOT_CONNECTED",
            "hermes_runtime_visibility": "UNKNOWN_NOT_CONNECTED"
        }

    def test_fresh_source_reconciles(self):
        report = reconcile(self.base(), NOW)
        self.assertEqual(report["state"], "RECONCILED")
        self.assertEqual(report["fresh_source_count"], 1)
        self.assertEqual(report["whole_system_completion"], "NOT_INFERRED")
        self.assertEqual(len(report["digest"]), 64)

    def test_stale_source_is_partial(self):
        payload = self.base()
        payload["sources"][0]["observed_at"] = "2026-08-06T10:00:00Z"
        payload["sources"][0]["freshness_seconds"] = 60
        report = reconcile(payload, NOW)
        self.assertEqual(report["state"], "PARTIAL")
        self.assertEqual(report["stale_source_count"], 1)

    def test_overlapping_writers_block(self):
        payload = self.base()
        payload["active_writers"] = [
            {"agent_id": "claude", "write_targets": ["service:8x8-control-fabric"]},
            {"agent_id": "hermes", "write_targets": ["service:8x8-control-fabric"]},
        ]
        report = reconcile(payload, NOW)
        self.assertEqual(report["state"], "BLOCKED_CONFLICT")
        self.assertEqual(report["conflicts"][0]["targets"], ["service:8x8-control-fabric"])


if __name__ == "__main__":
    unittest.main()
