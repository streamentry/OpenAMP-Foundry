# Release Dry-Run Reading Guide

## Purpose

The release dry-run (`make full-reproducibility-report`) generates a report
that summarizes pipeline state, benchmark results, simulation module status,
Phase 4 readiness, and honest limitations — **without publishing or tagging
anything**. It is a local preview, not a release.

## How to Run

```bash
make full-reproducibility-report
```

Output: `outputs/full_reproducibility_report.json` (machine-readable) and
`outputs/full_reproducibility_report.md` (human-readable).

## Reading the Report

### 1. Git State

Shows the current commit SHA and recent commits. If the SHA doesn't match
what you expected, you may be on the wrong branch.

### 2. Test Count

Shows the pytest collection count. A drop from the previous release is a
blocker — investigate before proceeding.

### 3. Benchmark Summaries

| Section | What to look for |
|---------|------------------|
| `benchmark_500` | AUROC should be consistent with METRICS_CURRENT.md |
| `cross_dataset` | DRAMP AUROC should be within 0.03 of primary |
| `simulation_ablation` | Verdict should be NO_IMPROVEMENT (expected) |
| `simulation_baselines` | Verdict should be NO_IMPROVEMENT (expected) |

### 4. Simulation Module Status

| Status | Meaning |
|--------|---------|
| `experimental` | Module does not beat cheap baselines — expected |
| `blocked` | Weighted mode correctly prevented by gate |
| `info available` | Users can inspect scores via `--simulation-mode info` |

### 5. Phase 4 Readiness

Each artifact is checked for existence. A ❌ means the file was not found.
Common causes:

- **lab_batch_pack**: Run `make lab-batch-pack` to generate the zip.
- **Other missing files**: Check if the path is correct in the report script.

If any artifact shows ❌ and it should exist, fix the path or regenerate.

### 6. Honest Limitations

This section lists known caveats. It is not a blocker — it is a truthfulness
check. Every limitation should be accurate and current.

## Interpreting the Verdict

| Status | Meaning |
|--------|---------|
| ✅ All checks pass | Pipeline is ready for review or release consideration |
| ⚠️ Warnings | Non-blocking issues (check each warning) |
| ❌ Blocker | Must be resolved before any public claim or release |

## What the Dry-Run Does NOT Do

- It does not publish anything.
- It does not tag or create a release.
- It does not send data anywhere.
- It does not change any files outside `outputs/`.

## Next Actions After a Clean Report

1. Review the honest limitations section for accuracy.
2. Run `make lab-batch-pack` if the zip is missing.
3. Verify benchmark numbers against `docs/evidence/METRICS_CURRENT.md`.
4. Proceed to human review or publication preparation per
   `docs/review/PUBLICATION_PACK.md`.
