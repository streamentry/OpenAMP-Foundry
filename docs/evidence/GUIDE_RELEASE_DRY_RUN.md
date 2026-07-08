# Final Local Release Dry-Run Script

The release dry-run is performed by:

```bash
make full-reproducibility-report
```

This generates `outputs/full_reproducibility_report.json` and `.md`.

## What It Checks
- Git state (SHA, recent commits)
- Test collection count
- Benchmark summaries (500-AMP, cross-dataset, simulations)
- Simulation module status (all experimental)
- Phase 4 readiness (8 artifact checks)
- Honest limitations (6 documented caveats)

## Reading the Report
See `docs/review/RELEASE_DRY_RUN_GUIDE.md` for a detailed reading guide.
See `docs/review/RELEASE_DRY_RUN_WALKTHROUGH.md` for an annotated walkthrough.
