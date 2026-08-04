#!/usr/bin/env python3
"""Validate an 8x8-compatible plugin manifest and print a deterministic receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas/plugins/8x8-plugin-manifest-v1.schema.json"


class PluginValidationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PluginValidationError(f"cannot read {path}: {type(exc).__name__}") from exc


def validate_plugin(manifest: Any, schema: Any) -> dict[str, Any]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.absolute_path))
    if errors:
        rendered = [
            {
                "path": "/" + "/".join(str(part) for part in error.absolute_path),
                "message": error.message,
            }
            for error in errors
        ]
        raise PluginValidationError(json.dumps(rendered, sort_keys=True))

    permissions = manifest["permissions"]
    tests = manifest["tests"]
    receipt = {
        "schema_version": "8x8.plugin-validation-receipt.v1",
        "plugin_id": manifest["plugin_id"],
        "version": manifest["version"],
        "manifest_digest": hashlib.sha256(canonical_bytes(manifest)).hexdigest(),
        "conformance_score": tests["conformance_score"],
        "default_permission": permissions["default"],
        "financial_authority": permissions["financial"],
        "network_scope_count": len(permissions["network"]),
        "secret_dependency_count": len(permissions["secrets"]),
        "rollback_tested": manifest["rollback"]["tested"],
        "eligible_for_catalog_review": (
            tests["conformance_score"] == 100
            and permissions["default"] == "DENY"
            and permissions["financial"] == "NONE"
            and manifest["rollback"]["tested"] is True
        ),
        "external_actions": 0,
    }
    receipt["receipt_digest"] = hashlib.sha256(canonical_bytes(receipt)).hexdigest()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        receipt = validate_plugin(load_json(args.manifest), load_json(args.schema))
    except PluginValidationError as exc:
        parser.error(str(exc))
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
