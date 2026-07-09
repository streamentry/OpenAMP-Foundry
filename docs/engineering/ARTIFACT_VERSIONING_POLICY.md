# Artifact Versioning Policy

## Purpose

External users need stability guarantees for schemas, evidence certificates,
and candidate manifests. Without a declared policy, any schema change can
silently break downstream consumers.

This document defines a structured versioning policy covering which artifacts
are versioned, the version format, breaking change rules, deprecation
timelines, and stability tiers.

## Scope

The following artifact types are versioned:

- **Schemas** (`schemas/*.schema.json`) — JSON Schema definitions for all
  machine-readable artifacts
- **Evidence certificates** — candidate evidence certificate outputs
- **Candidate manifests** — batch-level candidate manifests
- **Provenance records** — simulation provenance chain records
- **Benchmark cards** — machine-readable benchmark summaries
- **Model cards** — model metadata and capability descriptions

## Version format

All versioned artifacts use **MAJOR.MINOR.PATCH** (semantic versioning):

```
MAJOR.MINOR.PATCH
```

Where each component is a non-negative integer.

### Major version

Increment when a breaking change is made (see definition below).

### Minor version

Increment when functionality is added in a backward-compatible manner.

### Patch version

Increment when backward-compatible bug fixes, typo corrections, or
documentation improvements are made.

## Breaking change definition

A change is **breaking** if it would cause a valid artifact from the
previous version to fail validation, including:

- Removing or renaming a required field
- Changing a field's type in an incompatible way
- Adding a new required field
- Changing an enum constraint in a way that invalidates previously valid
  values (unless the change adds values only)
- Changing the structural composition rules of an artifact
- Changing the interpretation or meaning of an existing field

## Non-breaking changes

The following changes are NOT breaking:

- Adding optional fields
- Relaxing constraints (e.g., making a required field optional)
- Adding new enum values without removing existing ones
- Adding new metadata fields
- Improving validation error messages
- Adding documentation
- Adding examples

## Deprecation timeline

When a schema field, enum value, or artifact must be removed:

1. The deprecation is announced in the CHANGELOG entry for the minor
   version in which deprecation begins.
2. The deprecated element remains valid for at least **one full minor
   version cycle** after deprecation announcement.
3. Removal happens in the next MAJOR version, or after at least one
   minor version has passed since deprecation.
4. Deprecated elements SHOULD be clearly marked in the schema with a
   `deprecated` annotation or equivalent.

## Schema `$id` policy

Every stable schema MUST have a `$id` URI in the format:

```
https://openamp.org/schemas/<schema-name>/<version>
```

The `$id` MUST be updated when the MAJOR or MINOR version changes.
Schemas without an `$id` are considered experimental.

## Changelog requirement

Every schema version change MUST have a corresponding entry in
`docs/engineering/ARTIFACT_CHANGELOG.md`, recording:

- Date of change
- Schema name
- Old version and new version
- Type of change (MAJOR, MINOR, PATCH)
- Summary of what changed and why

## Stability tiers

### Tier 1 — Stable

Schemas that have a `$id` URI and are fully documented. These require a
MAJOR version bump for breaking changes. External consumers can rely on
Tier 1 artifacts for production workflows.

Requirements:
- `$id` URI set and versioned
- Documented in changelog
- Full test coverage for valid/invalid states
- Approval required for MAJOR version changes

### Tier 2 — Experimental

Schemas without a `$id` URI or in draft status. These may change without
notice but MUST be labeled `"experimental"` in their metadata or
documentation. External consumers should not depend on experimental
schemas for production use.

Requirements:
- Labeled as experimental
- Documented with known limitations
- May change at any time without deprecation notice

### Tier 3 — Internal

Artifacts not intended for external use. These carry no stability
promise. Internal tools and agents may change them freely.

Requirements:
- Clearly marked as internal
- Not documented for external consumption
- No deprecation notice required for changes

## Dry-lab-only statement

Artifact versioning applies to computational artifacts only. Versioning
does not change the computational or dry-lab nature of the results. All
artifacts remain dry-lab hypotheses requiring wet-lab validation.

Version numbers describe schema and format compatibility, not biological
validity, safety, or efficacy.

## Compliance

All new schemas added to `schemas/` MUST declare a stability tier. The
default tier for new schemas without explicit documentation is
**Tier 2 (Experimental)**.

Existing schemas added before this policy was adopted are Tier 1
(Stable) starting at version 1.0.0 if they have a `$id` field and
are in active use by the pipeline.
