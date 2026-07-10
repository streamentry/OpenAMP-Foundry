# Schema Version Migration Guide

This document explains how to update OpenAMP evidence schemas without breaking existing artifacts.

An artifact is any JSON file or Python dict that was serialized under a specific schema version. Once an artifact exists — in a results directory, a partner review packet, or an external database — its field names and validation rules are frozen. The schema may evolve; the artifact cannot.

## Versioning conventions

All OpenAMP schemas follow this numbering:

```
vMAJOR.MINOR.PATCH
```

| Increment | Meaning | Artifact impact |
|-----------|---------|----------------|
| MAJOR | Breaking change — field removed, type changed, validation rule tightened | Existing artifacts fail new validation |
| MINOR | Additive change — new optional field, new controlled vocab term | Existing artifacts remain valid |
| PATCH | Non-structural change — docstring, comment, formatting | No impact |

A schema's version is stored in its `$schema_version` field (for Python modules) or `$schema` / `"version"` field (for JSON schemas).

## Adding a field (MINOR)

1. Add the field with a default value or mark it optional.
2. Bump the MINOR version in the schema file.
3. Do not add the field to `REQUIRED_FIELDS` until the next MAJOR release.
4. Update the `validate_*()` function to accept artifacts that omit the field.
5. Add tests for both the old artifact shape (without the field) and the new shape (with the field).

Example: adding `synthesis_priority` to a batch outcome record:

```python
# Before (v1.0.0)
@dataclass
class BatchOutcomeSummary:
    batch_id: str
    total_candidates: int
    n_hits: int

# After (v1.1.0) — MINOR bump, field is optional
@dataclass
class BatchOutcomeSummary:
    batch_id: str
    total_candidates: int
    n_hits: int
    synthesis_priority: str = ""   # new optional field
```

## Removing a field (MAJOR)

Field removal is a breaking change. Follow this two-step process:

**Step 1 — deprecate (current release):**

```python
@dataclass
class OldSchema:
    legacy_field: str = ""   # DEPRECATED since v2.0. Use new_field instead.
    new_field: str = ""
```

Validation must continue to accept `legacy_field` without error.

**Step 2 — remove (next release):**

- Delete the field.
- Bump MAJOR version.
- Add a migration note to this document (see "Migration notes" below).
- Update `validate_*()` to reject or ignore the removed field.

## Renaming a field (MAJOR)

Renaming looks like removal + addition. Follow the same two-step deprecation process:

1. Add the new name alongside the old name.
2. In `validate_*()`, accept either name but warn when the old name is present.
3. In the next MAJOR release, remove the old name.

Do not rename a field in a PATCH or MINOR release.

## Tightening a validation rule (MAJOR)

Examples of tightening:
- Reducing the allowed vocabulary (`VALID_OUTCOMES` loses a term)
- Changing a field from optional to required
- Reducing a minimum length or count

Tightening is always a MAJOR bump because existing artifacts may fail the new rule.

Before tightening, audit all artifacts in `outputs/` and `tests/` for the old value. If any existing artifact uses the soon-to-be-invalid value:
1. Migrate it.
2. Open a PR for the migration.
3. Merge the migration PR before the schema PR.

## Loosening a validation rule (MINOR)

Examples of loosening:
- Adding a term to a controlled vocabulary
- Making a required field optional
- Increasing an allowed maximum

Loosening is safe; existing artifacts remain valid.

## Schema ID stability

Every schema has a stable `$id` or identifier prefix (e.g., `NRR-`, `BMC-`, `FAE-`). These IDs appear in external artifacts and cannot be changed without breaking cross-references.

Rules:
- Never change a schema `$id`.
- Never change a schema prefix (e.g., `FAE-` → `FASTA-`).
- Never rename a module at import path level without leaving a deprecated shim.

If a schema is so broken that its `$id` must change, create a new schema alongside the old one and deprecate the old one following [DEPRECATION_POLICY.md](DEPRECATION_POLICY.md).

## Migration notes

Append a row to this table whenever a MAJOR version bump removes or renames a field.

| Schema | Old version | New version | Removed/renamed field | Migration action |
|--------|-------------|-------------|----------------------|-----------------|
| (none yet) | — | — | — | — |

When filling in a migration row:
- **Schema**: the module name or schema file, e.g., `negative_result_record.py`
- **Old version**: the version before the breaking change
- **New version**: the version after
- **Removed/renamed field**: the old field name
- **Migration action**: what callers must do, e.g., "rename `legacy_id` to `record_id` in all NRR- artifacts"

## Testing migrations

Every MAJOR schema change must include:

1. A test that validates an artifact in the *old* format and confirms it now fails validation (the change is real).
2. A test that validates the migrated artifact and confirms it now passes.
3. An updated `test_test_count_regression.py` BASELINE.

Do not merge a MAJOR schema change without both tests.

## Agent rules

An agent MUST NOT:
- Bump the MAJOR version without a corresponding migration note in this document.
- Change a schema `$id` or controlled-vocabulary term without human review.
- Remove a field from a schema without first deprecating it in a prior PR.

An agent MAY:
- Add optional fields (MINOR bump).
- Add terms to controlled vocabularies (MINOR bump).
- Write migration tests.
- Append a row to the migration notes table when removing a deprecated field.

When in doubt about whether a change is MAJOR or MINOR, treat it as MAJOR and ask for human review.
