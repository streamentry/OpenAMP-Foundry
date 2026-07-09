"""Cross-artifact schema compatibility checks — prevents schema drift.

Validates that published artifact schemas share consistent conventions
and remain mutually compatible as they evolve.
Dry-lab only.
"""
from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any


SCHEMAS_DIR = Path(__file__).parent.parent.parent.parent / "schemas"

# Fields that MUST appear in every artifact schema
UNIVERSAL_REQUIRED_FIELDS: set[str] = {"dry_lab_only", "version"}

# Field naming conventions all schemas must respect
CONVENTION_CHECKS: dict[str, str] = {
    "dry_lab_only": "boolean const true",
    "version": "string matching MAJOR.MINOR.PATCH",
    "evidence_level": "integer in 1-6 when present",
}


@dataclass
class SchemaCompatibilityResult:
    schema_name: str
    schema_path: str
    passed: bool
    errors: list[str]
    warnings: list[str]
    dry_lab_only: bool = True


def load_schema(schema_path: Path) -> dict[str, Any]:
    with open(schema_path) as f:
        return json.load(f)


def check_schema_conventions(schema_name: str, schema: dict[str, Any]) -> SchemaCompatibilityResult:
    """Check that a schema follows universal conventions."""
    errors: list[str] = []
    warnings: list[str] = []
    schema_path = str(SCHEMAS_DIR / f"{schema_name}.schema.json")

    props = schema.get("properties", {})
    required = schema.get("required", [])

    for field in UNIVERSAL_REQUIRED_FIELDS:
        if field not in props:
            errors.append(f"Schema missing universal field '{field}' in properties")
        if field not in required:
            errors.append(f"Schema missing universal field '{field}' in required list")

    if "dry_lab_only" in props:
        dlo = props["dry_lab_only"]
        if dlo.get("const") is not True:
            errors.append("dry_lab_only must be a const: true in schema")

    if "version" in props:
        v = props["version"]
        if v.get("type") != "string":
            errors.append("version must be type: string in schema")

    if "evidence_level" in props:
        el = props["evidence_level"]
        if el.get("type") != "integer":
            errors.append("evidence_level must be type: integer when present")
        if el.get("minimum") != 1 or el.get("maximum") != 6:
            errors.append("evidence_level must have minimum: 1, maximum: 6")

    if schema.get("additionalProperties") is not False:
        warnings.append("Schema does not set additionalProperties: false -- schema drift risk")

    if "$schema" not in schema:
        warnings.append("Schema missing $schema declaration")
    elif "2020-12" not in schema.get("$schema", ""):
        warnings.append(f"Schema $schema is not Draft 2020-12: {schema.get('$schema')}")

    return SchemaCompatibilityResult(
        schema_name=schema_name,
        schema_path=schema_path,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def run_compatibility_check(schemas_dir: Path | None = None) -> dict[str, Any]:
    """Run compatibility checks on all *.schema.json files in the schemas directory."""
    target_dir = schemas_dir or SCHEMAS_DIR
    schema_files = sorted(target_dir.glob("*.schema.json"))
    results = []
    for sf in schema_files:
        name = sf.stem.replace(".schema", "")
        schema = load_schema(sf)
        result = check_schema_conventions(name, schema)
        results.append(result)

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    return {
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "all_passed": len(failed) == 0,
        "results": [vars(r) for r in results],
        "dry_lab_only": True,
    }
