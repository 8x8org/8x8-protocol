#!/usr/bin/env python3
"""8x8 OS 0.0.1 non-invasive convergence reconciliation watcher.

Consumes already-sanitized JSON snapshots or GitHub-derived receipt summaries and
produces a deterministic convergence report. It never connects to Termux, Ubuntu,
Claude, Hermes, services, databases, credentials, or wallets by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRODUCT_VERSION = "0.0.1"
REALITIES = {"PRIVATE_PAST", "PUBLIC_PRESENT", "FUTURE_LAB"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def now() -> datetime:
    return datetime.now(timezone.utc)


def load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def classify_source(source: dict[str, Any], moment: datetime) -> dict[str, Any]:
    required = {"source_id", "observed_at", "freshness_seconds", "evidence_state", "reality", "summary"}
    missing = sorted(required - source.keys())
    if missing:
        return {"source_id": source.get("source_id", "UNKNOWN"), "state": "INVALID", "missing": missing}
    if source["reality"] not in REALITIES:
        return {"source_id": source["source_id"], "state": "INVALID", "reason": "invalid reality"}
    age = max(0.0, (moment - parse_time(source["observed_at"])).total_seconds())
    freshness = float(source["freshness_seconds"])
    return {
        "source_id": source["source_id"],
        "state": "FRESH" if age <= freshness else "STALE",
        "age_seconds": age,
        "freshness_seconds": freshness,
        "evidence_state": source["evidence_state"],
        "reality": source["reality"],
        "summary": source["summary"],
        "source_digest": digest(source),
    }


def reconcile(payload: dict[str, Any], moment: datetime | None = None) -> dict[str, Any]:
    moment = moment or now()
    if payload.get("product_version") != PRODUCT_VERSION:
        raise ValueError("product_version must be 0.0.1")
    sources = [classify_source(item, moment) for item in payload.get("sources", [])]
    fresh = [item for item in sources if item.get("state") == "FRESH"]
    stale = [item for item in sources if item.get("state") == "STALE"]
    invalid = [item for item in sources if item.get("state") == "INVALID"]
    active_writers = payload.get("active_writers", [])
    conflicts = []
    for index, left in enumerate(active_writers):
        ltargets = set(map(str, left.get("write_targets", [])))
        for right in active_writers[index + 1:]:
            overlap = sorted(ltargets & set(map(str, right.get("write_targets", []))))
            if overlap:
                conflicts.append({
                    "left": left.get("agent_id", "UNKNOWN"),
                    "right": right.get("agent_id", "UNKNOWN"),
                    "targets": overlap,
                })
    report = {
        "product_version": PRODUCT_VERSION,
        "generated_at": moment.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "state": "BLOCKED_CONFLICT" if conflicts else ("PARTIAL" if stale or invalid else "RECONCILED"),
        "fresh_source_count": len(fresh),
        "stale_source_count": len(stale),
        "invalid_source_count": len(invalid),
        "active_writer_count": len(active_writers),
        "conflicts": conflicts,
        "sources": sources,
        "safe_next_action": (
            "Resolve overlapping write leases before mutation" if conflicts
            else "Refresh stale or invalid sources before promotion" if stale or invalid
            else "Proceed only with bounded, leased, reversible work"
        ),
        "claude_runtime_visibility": payload.get("claude_runtime_visibility", "UNKNOWN_NOT_CONNECTED"),
        "hermes_runtime_visibility": payload.get("hermes_runtime_visibility", "UNKNOWN_NOT_CONNECTED"),
        "whole_system_completion": "NOT_INFERRED",
    }
    report["digest"] = digest(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    report = reconcile(load(args.input))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if report["state"] == "BLOCKED_CONFLICT" else 0


if __name__ == "__main__":
    raise SystemExit(main())
