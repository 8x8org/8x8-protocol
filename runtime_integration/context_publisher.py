#!/usr/bin/env python3
"""8x8 Runtime Integration Kernel 0.0.1 context publisher.

Builds a deterministic, redacted Global Context Snapshot and live-state document
from local JSON inputs. It never reads secrets, private messages, database rows,
or arbitrary runtime files. Optional HMAC signing is for local integrity only,
not public identity. Production identity signatures belong behind an external
signer or hardware-backed key service.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PRODUCT_VERSION = "0.0.1"
REALITIES = {"PRIVATE_PAST", "PUBLIC_PRESENT", "FUTURE_LAB"}


def now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load(path: str | None, default: Any) -> Any:
    if not path:
        return default
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write(path: str, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    issued = now()
    snapshot: dict[str, Any] = {
        "product_version": PRODUCT_VERSION,
        "snapshot_id": args.snapshot_id,
        "issued_at": timestamp(issued),
        "expires_at": timestamp(issued + timedelta(seconds=args.ttl_seconds)),
        "reality": args.reality,
        "promotion_state": args.promotion_state,
        "node": load(args.node, {"node_id": args.node_id, "state": "REPORTED"}),
        "agents": load(args.agents, []),
        "missions": load(args.missions, []),
        "leases": load(args.leases, []),
        "services": load(args.services, []),
        "repositories": load(args.repositories, []),
        "deployments": load(args.deployments, []),
        "contradictions": load(args.contradictions, []),
        "evidence": load(args.evidence, []),
        "privacy": {
            "redacted": True,
            "secrets_included": False,
            "environment_values_included": False,
            "private_messages_included": False,
            "database_rows_included": False,
        },
    }
    unsigned = dict(snapshot)
    snapshot["digest"] = digest(unsigned)
    if args.hmac_key_env:
        key = os.environ.get(args.hmac_key_env)
        if not key:
            raise SystemExit(f"missing environment variable: {args.hmac_key_env}")
        snapshot["signature"] = {
            "scheme": "HMAC-SHA256-LOCAL-INTEGRITY-ONLY",
            "key_id": args.key_id,
            "value": hmac.new(key.encode(), canonical(unsigned), hashlib.sha256).hexdigest(),
        }
    else:
        snapshot["signature"] = {
            "scheme": "UNSIGNED_REFERENCE",
            "key_id": None,
            "value": None,
        }
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--reality", choices=sorted(REALITIES), default="PRIVATE_PAST")
    parser.add_argument("--promotion-state", choices=["PROTECTED_BETA"], default=None)
    parser.add_argument("--ttl-seconds", type=int, default=300)
    parser.add_argument("--node")
    parser.add_argument("--agents")
    parser.add_argument("--missions")
    parser.add_argument("--leases")
    parser.add_argument("--services")
    parser.add_argument("--repositories")
    parser.add_argument("--deployments")
    parser.add_argument("--contradictions")
    parser.add_argument("--evidence")
    parser.add_argument("--hmac-key-env")
    parser.add_argument("--key-id", default="local-reference")
    args = parser.parse_args()
    if args.ttl_seconds < 30 or args.ttl_seconds > 86400:
        raise SystemExit("ttl-seconds must be between 30 and 86400")
    snapshot = build_snapshot(args)
    atomic_write(args.output, snapshot)
    print(json.dumps({"output": args.output, "digest": snapshot["digest"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
