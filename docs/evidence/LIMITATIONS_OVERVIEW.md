# Honest Limitations Overview

OpenAMP Foundry is a serious computational project. It also has real
limitations. This page collects them in one place so readers and reviewers
can assess credibility without hunting through 50 documents.

---

## 1. Model Limitations

| Limitation | Detail | Status |
|---|---|---|
| Charge-dominated signal | Pipeline AUROC 0.7792 is inflated by charge density. Under exact charge-balanced synthetic controls, AUROC falls to 0.5103 (near chance). | Documented. `charge_bias` per candidate available. |
| Amphipathic-helix bias | Activity scorer assumes helical structure. Proline-rich, cysteine-rich (beta-sheet), and short AMPs are systematically undervalued (proline_rich AUROC 0.586 vs highly_cationic 0.958). | Per-family benchmark exists. Structural class floor in pilot-panel. |
| No sequence-order awareness | 24/31 features are composition-only. Only hydrophobic moment and dipeptide order score capture sequence order. Strict triage (scrambled control) AUROC 0.572. | Dipeptide order score added. Rich modeling deferred. |
| Simulation modules experimental | MembraneProxy and StructureProxy do not beat their cheapest heuristic baselines (0/4 signals). Weighted mode blocked by gate. | Info-only in `--simulation-mode info`. |

## 2. Data Limitations

| Limitation | Detail | Status |
|---|---|---|
| No wet-lab data | All scores are computational predictions. No antimicrobial activity has been demonstrated. | All output labeled as computational. |
| Benchmark decoys are synthetic | The 500 Swiss-Prot frequency decoys are not biologically validated negatives. Charge-balanced controls are synthetic. | Adversarial benchmarks track this gap. |
| Hemolysis reference small | 239 peptides (45 hemolytic, 125 selective after filtering) — moderate statistical power. HC50 values are literature-sourced with high inter-assay variability. | All confidence intervals reported. |

## 3. Benchmark Limitations

| Limitation | Detail | Status |
|---|---|---|
| AMP-vs-decoy is not the real task | Pipeline optimizes for multi-objective selection (active + safe + novel + synthesizable), not binary AMP/non-AMP discrimination. Charge density alone beats ensemble on the decoy task. | Easy baseline, charge-matched, and within-AMP benchmarks document this gap. |
| Within-AMP detection is weak | Best scorer (rich_selectivity) AUROC 0.7453 for hemolysis detection. No existing scorer passes strict triage (composition-matched decoys) at all three pairwise comparisons. | gate_triage passes standard triage; strict triage is the honest bar. |
| Small-k precision is high but unvalidated | Top-20 precision is 1.000 on the benchmark, but base rate in real screening is unknown (likely 1-10%). | Precision@k calibrated but caveated. |

## 4. Calibration Limitations

| Limitation | Detail | Status |
|---|---|---|
| No real calibration data | Recalibration pipeline (intake, gate, engine) is complete but has never been tested on real wet-lab results. | Synthetic data used for all tests. |
| Recalibration policy untested | `configs/recalibration_policy.yaml` defines 7 conditions and 5 prohibitions. None have been exercised against real data. | Gate logic is tested. Real exercise is pending. |

## 5. Safety and Review Limitations

| Limitation | Detail | Status |
|---|---|---|
| Safety scorer has blind spots | Melittin scores Safety=1.0 despite known hemolysis. Hemolysis cannot be predicted by current physicochemical scorers. | Mandatory hemolysis assay for all candidates. |
| No external expert review completed | Expert review template exists. No qualified domain expert has reviewed the candidate panel. | Template is ready. Review is pending. |
| Dual-use review not yet performed | Safety review template and dual-use checklist exist. No formal biosecurity review has been conducted. | Governance framework is in place. Review is pending. |

## 6. Reproducibility Limitations

| Limitation | Detail | Status |
|---|---|---|
| Some benchmark outputs are git-ignored | Generated files in `outputs/` are not committed. Regeneration requires running the pipeline. | `make regenerate-all` reproduces all outputs. |
| Random seeds not tracked per-run | Benchmark scripts use deterministic seeds, but run-level seed tracking is not automated. | Manual seed documentation in each script. |

---

## What This Does Not Mean

- **Not a failure.** Documentation of limitations is a sign of scientific maturity, not weakness.
- **Not an excuse.** Each limitation has a documented plan or mitigation.
- **Not a comprehensive risk register.** See `docs/evidence/RISK_REGISTER.md` for operational risks.

---

## Related Documents

- `docs/evidence/METRICS_CURRENT.md` — current benchmark numbers (single source of truth)
- `docs/evidence/BENCHMARK_GOVERNANCE.md` — benchmark policies
- `docs/evidence/SIMULATION_BENCHMARK.md` — simulation module evaluation
- `docs/evidence/CALIBRATION_POLICY.md` — recalibration gate rules
- `docs/evidence/EVIDENCE_CERTIFICATE.md` — per-candidate evidence schema
- `docs/review/EXPERT_REVIEW_PACK.md` — expert review guidelines
- `docs/trust/RISK_REGISTER.md` — operational risk register
