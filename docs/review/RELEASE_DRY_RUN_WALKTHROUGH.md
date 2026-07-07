# Guided Walkthrough: Release Dry-Run Report

This walkthrough uses a toy release dry-run report to explain each section.

```
make full-reproducibility-report
```

---

## Example: Full Report

```
Pipeline version: 0.1.0
Generated: 2026-07-07T12:00:00+00:00
Loops completed: 50
Git SHA: abc123def456
```

### What to check

| Field | Check | Pass/Fail |
|-------|-------|:---------:|
| `pipeline_version` | Matches expected release version | ✅ |
| `loops_completed` | Should be 50 | ✅ |
| `git SHA` | Confirms the right commit is being evaluated | ✅ |

---

## Phase Status

```
Phase 0 Structure: ✅ Complete
Phase 1 Benchmark Honesty: ✅ Complete
Phase 2 Calibration Engine: ✅ Complete
Phase 3 Virtual Assay: ✅ Complete
Phase 4 Wet Lab Readiness: ✅ Complete
```

All 5 phases should show Complete. Any phase with ❌ Incomplete
blocks the release.

---

## Benchmark Summaries

| Benchmark | Verdict | Action |
|-----------|:-------:|--------|
| 500-AMP AUROC | ~0.78 | Acceptable; charge-inflated (known limitation) |
| Cross-dataset | Within 0.03 of primary | ✅ |
| Simulation ablation | NO_IMPROVEMENT | ✅ Expected |
| Cheap-baseline comparison | 0/4 signals beat baselines | ✅ Expected |

If any benchmark shows a significant regression (AUROC drop > 0.02),
investigate before proceeding.

---

## Simulation Module Status

```
membrane_proxy:   experimental (does not beat cheap baselines)
structure_proxy:  experimental (does not beat cheap baselines)
weighted_mode:    blocked by simulation gate
cli_flag:         --simulation-mode info available for exploratory use
```

All simulation modules must remain `experimental`. If any module shows
`IMPROVEMENT` or `weighted` becomes unblocked, review the ablation
benchmark and gate decision before trusting.

---

## Phase 4 Readiness

| Artifact | Status | Action if Missing |
|----------|:------:|-------------------|
| Lab partner onboarding | ✅ | Create docs/review/LAB_PARTNER_ONBOARDING.md |
| Pass/fail criteria | ✅ | Create configs/wave1_pass_fail.yaml |
| Expert review template | ✅ | Create .github/ISSUE_TEMPLATE/expert_review.yml |
| Decision log schema | ✅ | Create schemas/decision_log.schema.json |
| Lab batch pack | ❌ | Run `make lab-batch-pack` |
| Analysis plan | ✅ | Create docs/research/WAVE1_ANALYSIS_PLAN.md |
| Data return validation | ✅ | Check scripts/validate_lab_data_return.py |
| Publication pack | ✅ | Check docs/review/PUBLICATION_PACK.md |

The lab batch pack (❌) is expected to be missing before generation.
Run `make lab-batch-pack` before sending to a partner.

---

## Honest Limitations

```
- no_wet_lab_data: No wet-lab assay data exists
- charge_dominated: Pipeline AUROC 0.7792 is charge-inflated
- simulation_experimental: All modules experimental
- benchmark_honesty: Collapses to 0.5103 under exact charge control
- compoundable: Value in multi-objective selection, not raw discrimination
```

These are not blockers — they are truthfulness requirements. Each must be
accurate. If a limitation is outdated or missing, update it.

---

## When NOT to Release

| Condition | Action |
|-----------|--------|
| Any Phase shows ❌ | Do not release — complete the phase first |
| Benchmark regression > 0.02 | Investigate and fix |
| Unexpected `IMPROVEMENT` in simulation | Review ablation evidence |
| Phase 4 artifact says ❌ but should exist | Fix path or regenerate |
| Limitations section is inaccurate | Update before release |

## Status: Read-Only

This report is a local preview. It does not:
- Publish anything
- Create a release tag
- Send data anywhere
- Modify files outside `outputs/`

## Next Steps After a Clean Walkthrough

1. Fix any ❌ artifacts (especially lab batch pack).
2. Review honest limitations for accuracy.
3. Run `make demo` to verify the pipeline still works.
4. Proceed to publication preparation per `docs/review/PUBLICATION_PACK.md`.
