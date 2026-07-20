# Lab Result Examples (SYNTHETIC)

> **ALL FILES IN THIS DIRECTORY ARE SYNTHETIC EXAMPLE DATA.**
>
> These JSON files demonstrate the calibration intake workflow. They are
> **not** real wet-lab measurements, do not correspond to any actual
> peptide synthesis, and must not be cited as experimental evidence of
> activity, safety, or any other biological property. They exist solely
> to exercise `openamp-foundry calibration-intake` end-to-end so future
> agents and reviewers can verify the workflow without real data.

## Files

| File | Assay | Purpose |
|------|-------|---------|
| `RES-SYN-001.json` | MIC (E. coli) | Synthetic active hit, controls pass |
| `RES-SYN-002.json` | hemolysis_RBC | Synthetic low hemolysis |
| `RES-SYN-003.json` | MIC (E. coli) | Synthetic inactive candidate |
| `RES-SYN-004.json` | hemolysis_RBC | Synthetic high hemolysis |
| `RES-SYN-005.json` | MIC (E. coli) | Synthetic active hit, controls fail |

## How to use

```bash
make lab-result-intake-example
```

This runs `openamp-foundry calibration-intake` against the synthetic panel
`examples/lab_results_panel.csv` and the synthetic lab results in this
directory. The output is written to `outputs/calibration_intake_example/`.

## When real lab data exists

Replace this directory with the real validated lab result JSON files,
where each file matches `schemas/lab_result.schema.json`. The pipeline
itself does not need to change — only the input data does.

For stronger join integrity, include the same
`computational_candidate_certificate_hash` column in the submitted panel CSV.
When that optional column is present, every tested candidate must have a
matching hash in its result record; mismatches or incomplete opted-in coverage
block clean calibration intake. Panels without the column remain supported but
are reported as certificate identity not available.

See `docs/WET_LAB_HANDOFF.md`, `docs/DECISION_RULES.md`, and
`docs/WAVE2_PLAN.md` for the workflow that converts these inputs into
recalibration decisions.
