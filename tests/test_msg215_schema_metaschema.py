#!/usr/bin/env python3
"""Validate every 8x8 JSON Schema against its declared meta-schema.

This test is intentionally read-only. It discovers schema files, verifies that each
uses the approved Draft 2020-12 dialect, enforces stable unique identifiers, and
asks jsonschema to validate the schema definitions themselves.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas"
APPROVED_DIALECT = "https://json-schema.org/draft/2020-12/schema"
APPROVED_ID_SCHEMES = {"https"}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: schema root must be an object")
    return value


def main() -> None:
    paths = sorted(SCHEMA_ROOT.rglob("*.schema.json"))
    assert paths, "no JSON Schema files discovered"

    seen_ids: dict[str, Path] = {}
    failures: list[str] = []

    for path in paths:
        relative = path.relative_to(ROOT)
        try:
            schema = load_json(path)

            dialect = schema.get("$schema")
            assert dialect == APPROVED_DIALECT, (
                f"declared $schema must be {APPROVED_DIALECT!r}, got {dialect!r}"
            )

            schema_id = schema.get("$id")
            assert isinstance(schema_id, str) and schema_id, "$id must be a nonempty string"
            parsed = urlparse(schema_id)
            assert parsed.scheme in APPROVED_ID_SCHEMES and parsed.netloc, (
                "$id must be an absolute HTTPS URI"
            )
            assert schema_id not in seen_ids, (
                f"duplicate $id also used by {seen_ids[schema_id].relative_to(ROOT)}"
            )
            seen_ids[schema_id] = path

            title = schema.get("title")
            assert isinstance(title, str) and title.strip(), "title must be nonempty"

            Draft202012Validator.check_schema(schema)
        except (AssertionError, json.JSONDecodeError, SchemaError) as exc:
            failures.append(f"{relative}: {exc}")

    if failures:
        raise SystemExit("Schema meta-validation failed:\n" + "\n".join(failures))

    print(f"validated {len(paths)} schemas against Draft 2020-12")


if __name__ == "__main__":
    main()
