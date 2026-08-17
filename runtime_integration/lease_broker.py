#!/usr/bin/env python3
"""Atomic file-backed lease broker for 8x8 OS 0.0.1 Beta.

Reference implementation only. It serializes lease acquisition with an advisory
lock, rejects overlapping active write targets, refreshes heartbeats, and records
release state. Production adapters must place this broker before mutations.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRODUCT_VERSION = "0.0.1"
ACTIVE_STATES = {"REQUESTED", "ACTIVE"}


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def now_text() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def load_registry(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, list):
        raise ValueError("lease registry must be a JSON array")
    return value


def atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def active(lease: dict[str, Any], moment: datetime) -> bool:
    return lease.get("state") in ACTIVE_STATES and parse_time(lease["expires_at"]) > moment


def validate(lease: dict[str, Any]) -> None:
    required = {
        "product_version", "lease_id", "task_id", "agent_id", "body_id",
        "node_id", "issued_at", "expires_at", "heartbeat_at", "write_targets",
        "rollback", "state", "reality"
    }
    missing = sorted(required - set(lease))
    if missing:
        raise ValueError(f"missing lease fields: {missing}")
    if lease["product_version"] != PRODUCT_VERSION:
        raise ValueError("product_version must be 0.0.1")
    if not lease["write_targets"]:
        raise ValueError("write_targets cannot be empty")
    if parse_time(lease["expires_at"]) <= parse_time(lease["issued_at"]):
        raise ValueError("lease expiry must follow issue time")


def acquire(candidate: dict[str, Any], registry: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    validate(candidate)
    moment = datetime.now(timezone.utc)
    requested = set(map(str, candidate["write_targets"]))
    conflicts = []
    retained = []
    for current in registry:
        validate(current)
        if active(current, moment):
            retained.append(current)
            if current["lease_id"] != candidate["lease_id"]:
                overlap = sorted(requested & set(map(str, current["write_targets"])))
                if overlap:
                    conflicts.append({"lease_id": current["lease_id"], "agent_id": current["agent_id"], "targets": overlap})
    if conflicts:
        return retained, conflicts
    candidate = dict(candidate)
    candidate["state"] = "ACTIVE"
    candidate["heartbeat_at"] = now_text()
    retained = [item for item in retained if item["lease_id"] != candidate["lease_id"]]
    retained.append(candidate)
    return sorted(retained, key=lambda item: item["lease_id"]), []


def mutate_registry(path: Path, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        registry = load_registry(path)
        if operation == "acquire":
            updated, conflicts = acquire(payload, registry)
            if conflicts:
                return {"ok": False, "conflicts": conflicts}
            atomic_write(path, updated)
            return {"ok": True, "lease": payload["lease_id"], "registry_size": len(updated)}
        lease_id = payload["lease_id"]
        found = False
        updated = []
        for lease in registry:
            if lease["lease_id"] == lease_id:
                found = True
                lease = dict(lease)
                if operation == "heartbeat":
                    lease["heartbeat_at"] = now_text()
                elif operation == "release":
                    lease["state"] = payload.get("state", "RELEASED")
                    lease["released_at"] = now_text()
                    lease["handoff_receipt"] = payload.get("handoff_receipt")
            updated.append(lease)
        if not found:
            return {"ok": False, "error": "lease_not_found"}
        atomic_write(path, updated)
        return {"ok": True, "lease": lease_id, "operation": operation}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    sub = parser.add_subparsers(dest="operation", required=True)
    acquire_cmd = sub.add_parser("acquire")
    acquire_cmd.add_argument("lease")
    heartbeat = sub.add_parser("heartbeat")
    heartbeat.add_argument("lease_id")
    release = sub.add_parser("release")
    release.add_argument("lease_id")
    release.add_argument("--state", choices=["RELEASED", "REVOKED", "EXPIRED"], default="RELEASED")
    release.add_argument("--handoff-receipt")
    args = parser.parse_args()
    if args.operation == "acquire":
        with Path(args.lease).open(encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        payload = {"lease_id": args.lease_id}
        if args.operation == "release":
            payload.update({"state": args.state, "handoff_receipt": args.handoff_receipt})
    result = mutate_registry(Path(args.registry), args.operation, payload)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
