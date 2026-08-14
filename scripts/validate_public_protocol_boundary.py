#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    "PUBLIC_PROTOCOL_BOUNDARY.md",
    "scripts/validate_public_protocol_boundary.py",
    ".github/workflows/validate-public-protocol-boundary.yml",
}
FORBIDDEN_PREFIXES = (
    "handoffs/",
    "private/",
    "internal/",
    "ops/",
    "runtime-private/",
)
FORBIDDEN_EXACT = {
    ".env",
    ".env.local",
    ".env.production",
}
PATTERNS = {
    "private_root_path": re.compile(rb"/root/", re.I),
    "private_android_path": re.compile(rb"/data/data/", re.I),
    "private_hermes_path": re.compile(rb"(?:^|[\\/])\.hermes(?:[\\/]|$)", re.I),
    "github_classic_token": re.compile(rb"\bgh[opsu]_[A-Za-z0-9]{30,}\b"),
    "github_fine_grained_token": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "openai_secret": re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "private_key": re.compile(rb"BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY"),
    "seed_assignment": re.compile(rb"(?i)\b(?:seed[_ -]?phrase|mnemonic|private[_ -]?key)\s*[:=]\s*[^\s<]{12,}"),
}


def tracked() -> list[str]:
    raw = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True).stdout
    return [x for x in raw.decode().split("\0") if x]


def main() -> int:
    violations: list[str] = []
    paths = tracked()
    for rel in paths:
        if rel in FORBIDDEN_EXACT:
            violations.append(f"forbidden exact path: {rel}")
        if any(rel.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            violations.append(f"forbidden path family: {rel}")
        if rel in EXCLUDED:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        payload = path.read_bytes()
        for label, pattern in PATTERNS.items():
            if pattern.search(payload):
                violations.append(f"{label}: {rel}")
    if violations:
        print("PUBLIC_PROTOCOL_BOUNDARY=FAIL")
        for v in sorted(set(violations)):
            print(f"- {v}")
        return 1
    print(f"PUBLIC_PROTOCOL_BOUNDARY=PASS tracked={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
