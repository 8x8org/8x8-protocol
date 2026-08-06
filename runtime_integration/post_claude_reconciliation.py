#!/usr/bin/env python3
"""Read-only post-Claude reconciliation for 8x8 OS 0.0.1 Beta.

Collects sanitized local facts, checks an optional Claude handoff packet, detects
lease overlap, and emits a deterministic activation-readiness report. It does
not start services, mutate databases, install packages, or expose secrets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "0.0.1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def run_safe(argv: list[str], cwd: str | None = None) -> dict[str, Any]:
    try:
        result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=15, check=False)
        return {"exit_code": result.returncode, "stdout": result.stdout.strip()[:8000], "stderr": result.stderr.strip()[:2000]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"exit_code": 127, "error": type(exc).__name__}


def repo_state(path: str) -> dict[str, Any]:
    root = Path(path)
    if not (root / ".git").exists():
        return {"path": path, "present": False}
    head = run_safe(["git", "rev-parse", "HEAD"], path)
    branch = run_safe(["git", "branch", "--show-current"], path)
    status = run_safe(["git", "status", "--porcelain=v1", "--untracked-files=all"], path)
    lines = [line for line in status.get("stdout", "").splitlines() if line]
    return {
        "path": path,
        "present": True,
        "head": head.get("stdout"),
        "branch": branch.get("stdout"),
        "changed_paths": len(lines),
        "status_digest": hashlib.sha256("\n".join(sorted(lines)).encode()).hexdigest(),
    }


def load(path: str | None, default: Any) -> Any:
    if not path:
        return default
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff")
    parser.add_argument("--leases")
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    handoff = load(args.handoff, None)
    leases = load(args.leases, [])
    active_targets: dict[str, str] = {}
    conflicts: list[dict[str, str]] = []
    for lease in leases:
        if lease.get("state") != "ACTIVE":
            continue
        for target in lease.get("write_targets", []):
            owner = active_targets.get(target)
            if owner and owner != lease.get("agent_id"):
                conflicts.append({"target": target, "first_agent": owner, "second_agent": str(lease.get("agent_id"))})
            else:
                active_targets[target] = str(lease.get("agent_id"))

    disk = shutil.disk_usage(os.environ.get("HOME", "/"))
    report = {
        "product_version": VERSION,
        "generated_at": now(),
        "mode": "READ_ONLY_RECONCILIATION",
        "host": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "storage": {"total": disk.total, "used": disk.used, "free": disk.free},
        "tools": {name: bool(shutil.which(name)) for name in ["git", "python3", "sha256sum", "sv", "sqlite3"]},
        "repositories": [repo_state(path) for path in args.repo],
        "claude_handoff": {
            "provided": handoff is not None,
            "status": handoff.get("status") if isinstance(handoff, dict) else "MISSING",
            "task_id": handoff.get("task_id") if isinstance(handoff, dict) else None,
            "digest": digest(handoff) if handoff is not None else None,
        },
        "active_lease_count": sum(1 for x in leases if x.get("state") == "ACTIVE"),
        "conflicts": conflicts,
        "activation_readiness": "BLOCKED_CONFLICT" if conflicts else ("READY_FOR_PLAN_ONLY" if handoff and handoff.get("status") in {"COMPLETED", "HANDOFF_READY"} else "WAIT_FOR_HANDOFF"),
        "prohibited_actions": ["service mutation", "database mutation", "package installation", "port exposure", "secret access"],
        "whole_system_complete": False,
    }
    report["digest"] = digest(report)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
