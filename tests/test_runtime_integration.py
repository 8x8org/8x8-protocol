from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from runtime_integration.context_publisher import build_snapshot
from runtime_integration.lease_broker import acquire


def ts(offset: int = 0) -> str:
    value = datetime.now(timezone.utc) + timedelta(seconds=offset)
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def lease(lease_id: str, target: str) -> dict:
    return {
        "product_version": "0.0.1",
        "lease_id": lease_id,
        "task_id": f"task-{lease_id}",
        "agent_id": f"agent-{lease_id}",
        "body_id": "cli",
        "node_id": "test-node",
        "issued_at": ts(-10),
        "expires_at": ts(300),
        "heartbeat_at": ts(-5),
        "write_targets": [target],
        "rollback": "restore fixture",
        "state": "ACTIVE",
        "reality": "PRIVATE_PAST",
        "promotion_state": None,
    }


class ContextPublisherTests(unittest.TestCase):
    def test_builds_redacted_digest_bound_snapshot(self) -> None:
        args = argparse.Namespace(
            snapshot_id="snapshot-test",
            node_id="node-test",
            reality="PRIVATE_PAST",
            promotion_state=None,
            ttl_seconds=300,
            node=None,
            agents=None,
            missions=None,
            leases=None,
            services=None,
            repositories=None,
            deployments=None,
            contradictions=None,
            evidence=None,
            hmac_key_env=None,
            key_id="reference",
        )
        snapshot = build_snapshot(args)
        self.assertEqual(snapshot["product_version"], "0.0.1")
        self.assertTrue(snapshot["privacy"]["redacted"])
        self.assertFalse(snapshot["privacy"]["secrets_included"])
        self.assertEqual(len(snapshot["digest"]), 64)
        self.assertEqual(snapshot["signature"]["scheme"], "UNSIGNED_REFERENCE")


class LeaseBrokerTests(unittest.TestCase):
    def test_rejects_overlapping_active_target(self) -> None:
        updated, conflicts = acquire(lease("candidate", "service:8x8-control-fabric"), [lease("existing", "service:8x8-control-fabric")])
        self.assertTrue(conflicts)
        self.assertEqual(conflicts[0]["targets"], ["service:8x8-control-fabric"])
        self.assertEqual(len(updated), 1)

    def test_accepts_non_overlapping_target(self) -> None:
        updated, conflicts = acquire(lease("candidate", "repo:8x8-protocol"), [lease("existing", "service:8x8-control-fabric")])
        self.assertFalse(conflicts)
        self.assertEqual({item["lease_id"] for item in updated}, {"candidate", "existing"})


if __name__ == "__main__":
    unittest.main()
