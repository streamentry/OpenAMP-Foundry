# Model Card: Default Ensemble Scorer

## Identity

| Field | Value |
|-------|-------|
| model_id | `openamp-ensemble-scorer` |
| name | Default Heuristic Ensemble Scorer |
| artifact_type | scorer |
| status | production |
| version | 0.1.0 |
| created_at | 2026-07-08 |
| maintainer | OpenAMP Foundry Contributors |
| release_status | open |
| proof_ladder_limit | multi_signal_candidate_evidence |

## Intended use

Rank candidate peptide sequences by predicted antimicrobial-likeness using a weighted sum of transparent physicochemical heuristics. The scorer is designed for:

- Pre-lab triage: which candidates are most worth reviewing?
- Batch ranking: within a single batch, which candidates rank highest?
- Safety gating: flag candidates with predicted toxicity or hemolysis risk.

## What it is not

- A calibrated probability estimator (Brier ~0.32, calibration slope ~0.43 — scores are ranking heuristics, not probabilities).
- A validated biological predictor.
- A replacement for any wet-lab assay.
- A tool for optimizing toxicity, virulence, or pathogenicity.

## Components

| Component | Weight (default) | What it measures |
|-----------|-----------------|------------------|
| activity_likeness | 0.40 | Physicochemical similarity to known AMPs |
| safety | 0.25 | Predicted low mammalian toxicity and hemolysis |
| synthesis | 0.15 | Synthesis feasibility (amino acid cost, oxidation risk) |
| novelty | 0.20 | Sequence dissimilarity from known references |

Also computes: boman_activity (Boman index), disagreement (scorer divergence), serum_stability, selectivity_proxy, hemolysis_risk, rich_selectivity, charge_bias.

## Known biases

| Bias | Evidence | Mitigation |
|------|----------|------------|
| Charge-dominated | Charge density alone AUROC 0.8166 beats ensemble 0.7792 | charge_bias flag in output |
| Anti-selective | Ensemble ranks hemolytic > selective on triage benchmark | --ranking-mode expert alternative |
| Helix-bias | Helical AMPs scored higher than proline-rich/sheet | Diversity selection compensates |
| Uncalibrated | Brier 0.32, slope 0.43 (over-confident) | Disclaimer in all reports |

## Dependencies

- Requires: `openamp_foundry.features.physchem` for feature extraction
- Requires: config file with weight values (default: `configs/pipeline.yaml`)

## Validation

| Benchmark | Result |
|-----------|--------|
| AMP-vs-decoy AUROC | 0.7792 (CI 95%: 0.7505–0.8065) |
| Cluster-split AUROC | 0.7610 (CI: 0.746–0.810) |
| Cross-dataset AUROC | 0.7803 (DRAMP independent set) |
| Brier score | 0.3178 (>0.25 = uninformative — not calibrated) |

See `docs/evidence/BENCHMARK_CARD.md` for full benchmark details.

## Limitations

1. Scores are not probabilities (see calibration note above).
2. All components are heuristic — they may not capture novel AMP mechanisms.
3. Benchmark performance is on known AMPs vs random decoys; real-world negatives may differ.
4. Expanding the feature set may not improve selection — each new component must beat cheap baselines.
