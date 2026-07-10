# Benchmark Card Guide (BMC-)

## Purpose

A `BenchmarkCard` is the machine-readable documentation contract for every benchmark in the pipeline. Before a benchmark can have ranking authority over candidates, it must have a corresponding BMC- record that documents:

1. What it measures (`measurement_target`)
2. How data is split (`split_strategy`)
3. What cheap baselines it must beat (`cheap_enemy_baselines`)
4. What evaluation metrics are used (`evaluation_metrics`)
5. What its known limitations are (`known_limitations`)

This prevents benchmark sprawl and enforces anti-hype governance at the schema level.

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `bmc_id` | str | Unique ID starting with `BMC-` |
| `pipeline_version` | str | Pipeline version when benchmark was defined |
| `benchmark_name` | str | Human-readable name |
| `measurement_target` | str | What's being measured (controlled vocab) |
| `split_strategy` | str | How data is split (controlled vocab) |
| `cheap_enemy_baselines` | List[str] | ≥1 cheap baseline this benchmark must beat |
| `evaluation_metrics` | List[str] | Evaluation metrics (controlled vocab) |
| `known_limitations` | List[str] | ≥1 documented limitation |
| `deprecated` | bool | Whether this benchmark is deprecated |
| `created_date` | str | ISO 8601 date |
| `last_updated_date` | str | ISO 8601 date |

## Optional Fields

| Field | Default | Description |
|-------|---------|-------------|
| `notes` | "" | Additional context (max 500 chars). Required when deprecated=True. |

## Validation Rules

1. `bmc_id` must start with `BMC-`
2. `pipeline_version` non-empty
3. `benchmark_name` non-empty
4. `measurement_target` in `VALID_MEASUREMENT_TARGETS`
5. `split_strategy` in `VALID_SPLIT_STRATEGIES`
6. `cheap_enemy_baselines` ≥1 entry, all non-empty strings
7. All entries in `cheap_enemy_baselines` non-empty
8. `evaluation_metrics` ≥1 entry, all in `VALID_EVALUATION_METRICS`
9. `known_limitations` ≥1 entry, all non-empty strings
10. `created_date` ISO 8601 format
11. `last_updated_date` ISO 8601 format
12. If `deprecated=True`, `notes` must explain why
13. `notes` ≤500 characters
14. `evaluation_metrics` entries in controlled vocab

## Anti-Hype Constraints

- A benchmark with no `cheap_enemy_baselines` cannot prove the method beats trivial rules. **Warnings** are emitted when only one cheap enemy is declared; two or more are preferred.
- Every benchmark has limitations. Documenting zero limitations is not allowed.
