#!/usr/bin/env python3
"""8x8 Coordination Kernel 0.0.1 reference implementation.

Public, implementation-neutral tooling for deterministic JSON canonicalization,
mission validation, lease-conflict checks, append-only events, evidence freshness,
contradiction tracking, public projection, and continuity-manifest verification.

This tool does not connect to the private 8x8 control plane and does not grant
runtime authority. Cryptographic identity/signing is represented by digest and
external-signature fields; production key custody belongs outside this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PRODUCT_VERSION = "0.0.1"
REALITIES = {"PRIVATE_PAST", "PUBLIC_PRESENT", "FUTURE_LAB"}
PROMOTION_STATES = {None, "PROTECTED_BETA"}
TERMINAL_STATES = {"COMPLETED", "FAILED", "BLOCKED", "REVOKED", "ROLLED_BACK"}


class KernelError(ValueError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write_json(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def require_fields(value: dict[str, Any], fields: Iterable[str], label: str) -> None:
    missing = [field for field in fields if field not in value or value[field] in (None, "", [])]
    if missing:
        raise KernelError(f"{label} missing required fields: {', '.join(missing)}")


def parse_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise KernelError(f"invalid RFC3339 timestamp: {value!r}") from exc


def validate_common(value: dict[str, Any], label: str) -> None:
    if value.get("product_version") != PRODUCT_VERSION:
        raise KernelError(f"{label}.product_version must be {PRODUCT_VERSION}")
    if value.get("reality") not in REALITIES:
        raise KernelError(f"{label}.reality must be one of {sorted(REALITIES)}")
    if value.get("promotion_state") not in PROMOTION_STATES:
        raise KernelError(f"{label}.promotion_state must be null or PROTECTED_BETA")


def validate_context(snapshot: dict[str, Any]) -> dict[str, Any]:
    require_fields(snapshot, ["product_version", "snapshot_id", "issued_at", "expires_at", "reality", "estate"], "context")
    validate_common(snapshot, "context")
    issued = parse_time(snapshot["issued_at"])
    expires = parse_time(snapshot["expires_at"])
    if expires <= issued:
        raise KernelError("context.expires_at must be later than issued_at")
    unsigned = {key: val for key, val in snapshot.items() if key not in {"digest", "signature"}}
    expected = sha256(unsigned)
    if snapshot.get("digest") not in (None, expected):
        raise KernelError("context digest mismatch")
    result = dict(snapshot)
    result["digest"] = expected
    return result


def target_set(lease: dict[str, Any]) -> set[str]:
    return {str(item) for item in lease.get("write_targets", [])}


def active(lease: dict[str, Any], at: datetime) -> bool:
    if lease.get("state") not in {"REQUESTED", "ACTIVE"}:
        return False
    return parse_time(lease["expires_at"]) > at


def validate_lease(lease: dict[str, Any]) -> None:
    require_fields(lease, ["product_version", "lease_id", "task_id", "agent_id", "body_id", "node_id", "issued_at", "expires_at", "heartbeat_at", "write_targets", "rollback", "state", "reality"], "lease")
    validate_common(lease, "lease")
    if not isinstance(lease["write_targets"], list) or not lease["write_targets"]:
        raise KernelError("lease.write_targets must be a non-empty list")
    if parse_time(lease["expires_at"]) <= parse_time(lease["issued_at"]):
        raise KernelError("lease expiry must be after issue time")
    if parse_time(lease["heartbeat_at"]) < parse_time(lease["issued_at"]):
        raise KernelError("lease heartbeat cannot precede issue time")


def find_conflicts(candidate: dict[str, Any], registry: list[dict[str, Any]], at: datetime | None = None) -> list[dict[str, Any]]:
    validate_lease(candidate)
    moment = at or datetime.now(timezone.utc)
    candidate_targets = target_set(candidate)
    conflicts: list[dict[str, Any]] = []
    for lease in registry:
        validate_lease(lease)
        if lease["lease_id"] == candidate["lease_id"] or not active(lease, moment):
            continue
        overlap = sorted(candidate_targets & target_set(lease))
        if overlap:
            conflicts.append({"lease_id": lease["lease_id"], "agent_id": lease["agent_id"], "targets": overlap})
    return conflicts


def validate_mission(mission: dict[str, Any], context: dict[str, Any] | None = None, leases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    require_fields(mission, ["product_version", "mission_id", "owner_intent", "context_digest", "agent", "authority_lease_id", "capabilities", "targets", "acceptance_tests", "cleanup", "rollback", "status", "reality"], "mission")
    validate_common(mission, "mission")
    require_fields(mission["agent"], ["agent_id", "body_id", "node_id"], "mission.agent")
    if not mission["acceptance_tests"]:
        raise KernelError("mission.acceptance_tests cannot be empty")
    if context is not None:
        validated_context = validate_context(context)
        if mission["context_digest"] != validated_context["digest"]:
            raise KernelError("mission context_digest does not match supplied context")
    if leases is not None:
        matching = [lease for lease in leases if lease.get("lease_id") == mission["authority_lease_id"]]
        if len(matching) != 1:
            raise KernelError("mission authority lease was not found exactly once")
        lease = matching[0]
        validate_lease(lease)
        if lease["task_id"] != mission["mission_id"]:
            raise KernelError("mission ID does not match lease task ID")
        for key in ("agent_id", "body_id", "node_id"):
            if mission["agent"][key] != lease[key]:
                raise KernelError(f"mission agent binding mismatch: {key}")
        uncovered = sorted(set(map(str, mission["targets"])) - target_set(lease))
        if uncovered:
            raise KernelError(f"mission targets not covered by lease: {uncovered}")
    if mission["status"] in TERMINAL_STATES:
        require_fields(mission, ["events", "artifacts", "test_results", "final_receipt"], "terminal mission")
        if mission["status"] == "COMPLETED" and not all(bool(result.get("passed")) for result in mission["test_results"]):
            raise KernelError("completed mission contains a failed acceptance test")
    unsigned = {key: val for key, val in mission.items() if key not in {"digest", "signature"}}
    result = dict(mission)
    result["digest"] = sha256(unsigned)
    return result


def append_event(log_path: str | Path, event: dict[str, Any]) -> dict[str, Any]:
    require_fields(event, ["event_id", "event_type", "occurred_at", "actor_id", "subject_id", "reality", "evidence_state"], "event")
    if event["reality"] not in REALITIES:
        raise KernelError("event reality is invalid")
    path = Path(log_path)
    previous_digest = None
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            previous_digest = json.loads(lines[-1])["digest"]
    unsigned = dict(event)
    unsigned["previous_digest"] = previous_digest
    unsigned["product_version"] = PRODUCT_VERSION
    record = dict(unsigned)
    record["digest"] = sha256(unsigned)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return record


def check_freshness(record: dict[str, Any], at: datetime | None = None) -> dict[str, Any]:
    require_fields(record, ["observed_at", "freshness_seconds"], "freshness record")
    moment = at or datetime.now(timezone.utc)
    observed = parse_time(record["observed_at"])
    age = max(0.0, (moment - observed).total_seconds())
    limit = float(record["freshness_seconds"])
    return {"age_seconds": age, "freshness_seconds": limit, "fresh": age <= limit, "state": "FRESH" if age <= limit else "STALE"}


def validate_contradiction(value: dict[str, Any]) -> dict[str, Any]:
    require_fields(value, ["contradiction_id", "claims", "severity", "safe_assumption", "resolver", "status", "opened_at"], "contradiction")
    if len(value["claims"]) < 2:
        raise KernelError("contradiction requires at least two claims")
    if value["status"] == "RESOLVED":
        require_fields(value, ["resolution_receipt", "resolved_at"], "resolved contradiction")
    result = dict(value)
    result["digest"] = sha256({key: val for key, val in value.items() if key != "digest"})
    return result


def public_projection(private_state: dict[str, Any], allowlist: dict[str, Any]) -> dict[str, Any]:
    require_fields(allowlist, ["allowed_top_level", "blocked_terms"], "projection policy")
    output = {key: private_state[key] for key in allowlist["allowed_top_level"] if key in private_state}
    serialized = json.dumps(output, sort_keys=True).lower()
    matches = [term for term in allowlist["blocked_terms"] if term.lower() in serialized]
    if matches:
        raise KernelError(f"public projection contains blocked terms: {matches}")
    output["projection"] = {"product_version": PRODUCT_VERSION, "generated_at": now_utc(), "source_digest": sha256(private_state), "truth": "PUBLIC_SAFE_PROJECTION"}
    output["digest"] = sha256(output)
    return output


def continuity_manifest(paths: list[str]) -> dict[str, Any]:
    files = []
    for item in sorted(paths):
        path = Path(item)
        data = path.read_bytes()
        files.append({"path": item, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {"product_version": PRODUCT_VERSION, "created_at": now_utc(), "files": files}
    manifest["digest"] = sha256(manifest)
    return manifest


def verify_continuity(manifest: dict[str, Any]) -> list[str]:
    errors = []
    for item in manifest.get("files", []):
        path = Path(item["path"])
        if not path.is_file():
            errors.append(f"missing:{item['path']}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item["sha256"]:
            errors.append(f"digest_mismatch:{item['path']}")
    return errors


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="8x8-kernel")
    sub = parser.add_subparsers(dest="command", required=True)

    digest = sub.add_parser("digest")
    digest.add_argument("json_file")

    context = sub.add_parser("context-validate")
    context.add_argument("snapshot")

    lease = sub.add_parser("lease-check")
    lease.add_argument("candidate")
    lease.add_argument("registry")

    mission = sub.add_parser("mission-validate")
    mission.add_argument("mission")
    mission.add_argument("--context")
    mission.add_argument("--leases")

    event = sub.add_parser("event-append")
    event.add_argument("log")
    event.add_argument("event")

    freshness = sub.add_parser("freshness-check")
    freshness.add_argument("record")

    contradiction = sub.add_parser("contradiction-validate")
    contradiction.add_argument("record")

    projection = sub.add_parser("project-public")
    projection.add_argument("private_state")
    projection.add_argument("policy")
    projection.add_argument("output")

    continuity = sub.add_parser("continuity-create")
    continuity.add_argument("output")
    continuity.add_argument("paths", nargs="+")

    verify = sub.add_parser("continuity-verify")
    verify.add_argument("manifest")

    args = parser.parse_args(argv)
    try:
        if args.command == "digest":
            emit({"sha256": sha256(load_json(args.json_file))})
        elif args.command == "context-validate":
            emit(validate_context(load_json(args.snapshot)))
        elif args.command == "lease-check":
            candidate = load_json(args.candidate)
            registry = load_json(args.registry)
            conflicts = find_conflicts(candidate, registry)
            emit({"valid": not conflicts, "conflicts": conflicts})
            if conflicts:
                return 2
        elif args.command == "mission-validate":
            context_value = load_json(args.context) if args.context else None
            leases_value = load_json(args.leases) if args.leases else None
            emit(validate_mission(load_json(args.mission), context_value, leases_value))
        elif args.command == "event-append":
            emit(append_event(args.log, load_json(args.event)))
        elif args.command == "freshness-check":
            result = check_freshness(load_json(args.record))
            emit(result)
            if not result["fresh"]:
                return 3
        elif args.command == "contradiction-validate":
            emit(validate_contradiction(load_json(args.record)))
        elif args.command == "project-public":
            result = public_projection(load_json(args.private_state), load_json(args.policy))
            atomic_write_json(args.output, result)
            emit(result)
        elif args.command == "continuity-create":
            result = continuity_manifest(args.paths)
            atomic_write_json(args.output, result)
            emit(result)
        elif args.command == "continuity-verify":
            errors = verify_continuity(load_json(args.manifest))
            emit({"valid": not errors, "errors": errors})
            if errors:
                return 4
    except (KernelError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
