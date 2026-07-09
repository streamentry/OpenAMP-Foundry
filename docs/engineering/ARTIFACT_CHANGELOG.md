# Artifact Changelog

> Machine-readable changelog for evidence certificates and computational
> artifacts. External tools can parse this document to detect breaking
> changes and adapt consumers.
>
> All entries are for dry-lab computational artifacts only — they describe
> schema and format changes, not biological findings.

## Unreleased

- (no pending changes)

## [1.0.0] - 2026-07-09

### Added

- **candidate_manifest** — initial schema (14 required fields: candidate_id,
  sequence, evidence_level, scopes, scores, uncertainty, source_modules,
  calibration_set, safety_flags, provenance_run_id, dry_lab_only, version,
  created_at, notes). Phase I I2. Entry type: added. Breaking: false.

- **benchmark_card** — initial schema (15 required fields: benchmark_id,
  benchmark_name, version, date, metric, metric_value, baseline_name,
  baseline_value, delta, beats_baseline, dataset, dataset_size, scope,
  caveats, dry_lab_only). Phase I I3. Entry type: added. Breaking: false.

- **simulation_result** — initial schema (8 required fields: module, version,
  scope, scores, uncertainty, calibration_set, validated_against, notes).
  Phase H H2. Entry type: added. Breaking: false.

- **simulation_module_registry** — initial schema with module metadata
  (module_id, name, description, status, evidence_level, baseline_comparison,
  scope, maintainer, notes). Phase H H1. Entry type: added. Breaking: false.

- **artifact_versioning_policy** — initial versioning policy document
  covering stability tiers, SemVer format, breaking change rules, and
  deprecation timeline. Phase I I1. Entry type: added. Breaking: false.
