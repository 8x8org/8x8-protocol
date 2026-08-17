import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from coordination_kernel.coordination_kernel import (
    KernelError,
    append_event,
    check_freshness,
    continuity_manifest,
    find_conflicts,
    public_projection,
    sha256,
    validate_context,
    validate_contradiction,
    validate_mission,
    verify_continuity,
)


def ts(offset_seconds=0):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat().replace("+00:00", "Z")


class CoordinationKernelTests(unittest.TestCase):
    def context(self):
        return {
            "product_version": "0.0.1",
            "snapshot_id": "ctx-1",
            "issued_at": ts(-10),
            "expires_at": ts(600),
            "reality": "PRIVATE_PAST",
            "promotion_state": None,
            "estate": {"repositories": 16},
        }

    def lease(self, lease_id="lease-1", target="repo:a/path", agent="claude"):
        return {
            "product_version": "0.0.1",
            "lease_id": lease_id,
            "task_id": "mission-1",
            "agent_id": agent,
            "body_id": f"{agent}-cli",
            "node_id": "termux-ubuntu",
            "issued_at": ts(-20),
            "expires_at": ts(600),
            "heartbeat_at": ts(-2),
            "write_targets": [target],
            "rollback": "git reset --hard <known-good>",
            "state": "ACTIVE",
            "reality": "PRIVATE_PAST",
            "promotion_state": None,
        }

    def test_context_digest_is_deterministic(self):
        validated = validate_context(self.context())
        self.assertEqual(validated["digest"], validate_context(validated)["digest"])

    def test_conflicting_active_lease_is_detected(self):
        conflicts = find_conflicts(self.lease("candidate", agent="hermes"), [self.lease()])
        self.assertEqual(conflicts[0]["targets"], ["repo:a/path"])

    def test_nonoverlapping_lease_is_allowed(self):
        candidate = self.lease("candidate", "repo:b/path", "hermes")
        self.assertEqual(find_conflicts(candidate, [self.lease()]), [])

    def test_mission_binds_context_agent_lease_and_targets(self):
        context = validate_context(self.context())
        lease = self.lease()
        mission = {
            "product_version": "0.0.1",
            "mission_id": "mission-1",
            "owner_intent": "Apply a bounded test change",
            "context_digest": context["digest"],
            "agent": {"agent_id": "claude", "body_id": "claude-cli", "node_id": "termux-ubuntu"},
            "authority_lease_id": "lease-1",
            "capabilities": ["git-write"],
            "targets": ["repo:a/path"],
            "acceptance_tests": [{"id": "t1", "command": "python -m unittest"}],
            "cleanup": "remove temporary files",
            "rollback": "git reset --hard <known-good>",
            "status": "EXECUTING",
            "reality": "PRIVATE_PAST",
            "promotion_state": None,
        }
        validated = validate_mission(mission, context, [lease])
        self.assertEqual(len(validated["digest"]), 64)

    def test_completed_mission_cannot_hide_failed_test(self):
        context = validate_context(self.context())
        lease = self.lease()
        mission = {
            "product_version": "0.0.1",
            "mission_id": "mission-1",
            "owner_intent": "Test",
            "context_digest": context["digest"],
            "agent": {"agent_id": "claude", "body_id": "claude-cli", "node_id": "termux-ubuntu"},
            "authority_lease_id": "lease-1",
            "capabilities": ["git-write"],
            "targets": ["repo:a/path"],
            "acceptance_tests": [{"id": "t1"}],
            "cleanup": "done",
            "rollback": "known-good",
            "status": "COMPLETED",
            "reality": "PRIVATE_PAST",
            "promotion_state": None,
            "events": [],
            "artifacts": [],
            "test_results": [{"id": "t1", "passed": False}],
            "final_receipt": {"id": "r1"},
        }
        with self.assertRaises(KernelError):
            validate_mission(mission, context, [lease])

    def test_event_log_is_hash_linked(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "events.jsonl"
            base = {
                "event_type": "MISSION_STARTED",
                "occurred_at": ts(),
                "actor_id": "claude",
                "subject_id": "mission-1",
                "reality": "PRIVATE_PAST",
                "evidence_state": "OBSERVED",
            }
            first = append_event(log, {**base, "event_id": "e1"})
            second = append_event(log, {**base, "event_id": "e2"})
            self.assertEqual(second["previous_digest"], first["digest"])

    def test_freshness_marks_stale(self):
        result = check_freshness({"observed_at": ts(-100), "freshness_seconds": 5})
        self.assertFalse(result["fresh"])

    def test_contradiction_requires_two_claims(self):
        with self.assertRaises(KernelError):
            validate_contradiction({
                "contradiction_id": "c1",
                "claims": [{"value": "one"}],
                "severity": "HIGH",
                "safe_assumption": "UNKNOWN",
                "resolver": "hermes",
                "status": "OPEN",
                "opened_at": ts(),
            })

    def test_projection_is_allowlisted_and_digest_bound(self):
        private = {
            "product_version": "0.0.1",
            "reality": "PUBLIC_PRESENT",
            "public_products": ["Truth Console"],
            "private_runtime": {"secret": "excluded"},
        }
        policy = {"allowed_top_level": ["product_version", "reality", "public_products"], "blocked_terms": ["seed phrase"]}
        projection = public_projection(private, policy)
        self.assertNotIn("private_runtime", projection)
        self.assertEqual(len(projection["digest"]), 64)

    def test_continuity_manifest_detects_change(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            path.write_text("{}", encoding="utf-8")
            manifest = continuity_manifest([str(path)])
            self.assertEqual(verify_continuity(manifest), [])
            path.write_text('{"changed":true}', encoding="utf-8")
            self.assertTrue(verify_continuity(manifest))

    def test_canonical_digest_ignores_key_order(self):
        self.assertEqual(sha256({"a": 1, "b": 2}), sha256({"b": 2, "a": 1}))


if __name__ == "__main__":
    unittest.main()
