#!/usr/bin/env python3
"""Redacted read-only estate collector for 8x8 OS 0.0.1.

The collector intentionally gathers only low-risk host facts. It does not read
environment values, credentials, private messages, database rows, wallet data,
or file contents. Output is a local snapshot that must be reviewed before any
public projection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRODUCT_VERSION = "0.0.1"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def command(args: list[str], timeout: int = 4) -> dict[str, Any]:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "available": True,
            "exit_code": completed.returncode,
            "stdout": completed.stdout[:20000],
            "stderr": completed.stderr[:4000],
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": type(exc).__name__}


def git_state(path: Path) -> dict[str, Any]:
    if not (path / ".git").exists():
        return {"path": str(path), "git": False}
    head = command(["git", "-C", str(path), "rev-parse", "HEAD"])
    branch = command(["git", "-C", str(path), "branch", "--show-current"])
    status = command(["git", "-C", str(path), "status", "--porcelain=v1", "--untracked-files=all"])
    return {
        "path": str(path),
        "git": True,
        "head": head.get("stdout", "").strip() or None,
        "branch": branch.get("stdout", "").strip() or None,
        "changed_path_count": len([line for line in status.get("stdout", "").splitlines() if line]),
        "status_digest": hashlib.sha256("\n".join(sorted(status.get("stdout", "").splitlines())).encode()).hexdigest(),
    }


def service_names() -> list[str]:
    names: set[str] = set()
    for root in (Path("/etc/systemd/system"), Path("/data/data/com.termux/files/usr/var/service")):
        if root.is_dir():
            for child in root.iterdir():
                if child.name.startswith("."):
                    continue
                names.add(child.name)
    return sorted(names)


def collect(repo_paths: list[str]) -> dict[str, Any]:
    usage = shutil.disk_usage(Path.home())
    snapshot = {
        "product_version": PRODUCT_VERSION,
        "snapshot_id": f"estate-{int(datetime.now(timezone.utc).timestamp())}",
        "observed_at": now_utc(),
        "reality": "PRIVATE_PAST",
        "promotion_state": None,
        "collector": {
            "mode": "READ_ONLY_REDACTED",
            "hostname_digest": hashlib.sha256(socket.gethostname().encode()).hexdigest(),
            "environment_values_read": False,
            "file_contents_read": False,
            "database_rows_read": False,
            "credentials_read": False,
        },
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "storage": {
            "home_total_bytes": usage.total,
            "home_used_bytes": usage.used,
            "home_free_bytes": usage.free,
        },
        "repositories": [git_state(Path(path).expanduser().resolve()) for path in repo_paths],
        "service_inventory": {
            "names": service_names(),
            "status": "INVENTORIED_NOT_HEALTH_VERIFIED",
        },
        "tools": {
            name: bool(shutil.which(name))
            for name in ("git", "python3", "node", "npm", "docker", "podman", "sqlite3", "ffmpeg")
        },
    }
    unsigned = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    snapshot["digest"] = hashlib.sha256(unsigned).hexdigest()
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[], help="Repository path to inventory; may be repeated")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    snapshot = collect(args.repo)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target), "digest": snapshot["digest"], "mode": "READ_ONLY_REDACTED"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
