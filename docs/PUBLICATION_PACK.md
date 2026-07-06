# Publication Pack Checklist

**Purpose:** What to include in a public release of OpenAMP Foundry results.
A reviewer should be able to reproduce all findings from the contents of this pack.

---

## 1. Pipeline Code and Version

- [ ] Git commit SHA of the pipeline version used.
- [ ] `configs/pipeline.yaml` and `configs/phase3.yaml` used for scoring.
- [ ] List of all Python package dependencies with versions (`pip freeze` or `pyproject.toml`).
- [ ] Instructions to recreate the Python environment (`make install` or `pip install -e .[dev]`).

---

## 2. Input Data

- [ ] Candidate sequences (FASTA or CSV).
- [ ] Reference AMP database version and download instructions (APD6, DRAMP, UniProt).
- [ ] Decoy sequences used for benchmarking.
- [ ] Dataset cards for each dataset (source, license, date, known biases).
- [ ] Input hashes (SHA-256) for reproducibility verification.

---

## 3. Scoring and Ranking Outputs

- [ ] Per-candidate scores (JSONL or CSV): ensemble, activity, safety, synthesis, novelty.
- [ ] Per-candidate simulation scores (if `--simulation-mode info` was used).
- [ ] Selection rule used (`configs/pipeline.yaml` weights).
- [ ] Ranked candidate list with selection reasons.
- [ ] Evidence certificates (JSON) for all selected candidates.

---

## 4. Benchmark Results

- [ ] Expanded benchmark (500 AMP + 500 decoy): AUROC, AUPRC, CI.
- [ ] Cluster-split benchmark with cluster-aware CI.
- [ ] Easy baseline comparison (charge density vs pipeline).
- [ ] Cross-dataset generalization (DRAMP).
- [ ] Per-family breakdown (6 structural classes).
- [ ] Precision@k calibration.
- [ ] Simulation ablation results (AMP-vs-decoy + within-AMP).
- [ ] Simulation cheap-baseline comparison (0/4 signals beat baselines).
- [ ] Benchmark gate verdict (all metrics within tolerance).

---

## 5. Candidate Panel

- [ ] Final panel CSV with candidate IDs, sequences, scores, and selection reasons.
- [ ] Diversity clustering report.
- [ ] Novelty report against known AMP references (BLOSUM62 local alignment).
- [ ] Broad novelty check results (72-AMP or 27k-sequence reference).
- [ ] Toxicity / hemolysis risk report.
- [ ] Synthesis feasibility report.
- [ ] Pre-registered selection rule document.
- [ ] Evidence certificates for all selected candidates.

---

## 6. Wet-Lab Results (if available)

- [ ] Raw lab result JSONs (one per candidate per assay).
- [ ] Pass/fail criteria check output (`check_wave1_pass_fail.py` verdict).
- [ ] Primary analysis results (MIC ≤ 32 hit rate).
- [ ] Secondary analysis (selectivity index, TI > 10).
- [ ] Exploratory analysis (per-family, structural class, calibration).
- [ ] Positive control results.
- [ ] Negative results archive entries.
- [ ] Lab batch pack zip used.

---

## 7. Calibration and Active Learning (if available)

- [ ] Calibration intake report (`calibration-intake` output).
- [ ] Recalibration gate verdict (`recalibration-gate` output).
- [ ] Weight update proposal (if gate passed).
- [ ] Decision log entries for each human review decision.
- [ ] Batch-2 selection manifest (if applicable).

---

## 8. Reproducibility Evidence

- [ ] Run manifest JSON for each pipeline run (input hashes, config hash, outputs).
- [ ] `make regenerated-all` output (all derived outputs from versioned inputs).
- [ ] Benchmark gate output (`outputs/metrics_snapshot.json`).
- [ ] Pipeline version string (`openamp-foundry --version`).
- [ ] Random seed documentation (all benchmark scripts use deterministic seeds).

---

## 9. Negative Results

- [ ] Pre-selection rejects (candidates eliminated by gates).
- [ ] Selected-but-untested candidates.
- [ ] Lab-tested inactives (MIC > 32 µg/mL).
- [ ] Lab-tested toxic (TI < 2).
- [ ] Control failures.
- [ ] Simulation ablation negative results (0/4 signals beat baselines).
- [ ] All entries in `outputs/negative_result_archive.csv` format.

---

## 10. Safety and Governance

- [ ] Safety review documentation (dual-use, biosecurity).
- [ ] Decision log entries for all human review decisions.
- [ ] Pre-registration documents (assay preregistration, analysis plan).
- [ ] Model release policy compliance (no unscreened weights shipped).
- [ ] Responsible use statement.
- [ ] License information (Apache-2.0 for code, CC BY 4.0 for docs).

---

## 11. README for Reproduction

A top-level README in the release package should include:

1. One-paragraph summary of what was done.
2. System requirements (Python 3.11+, RAM, OS).
3. Installation instructions.
4. Command to regenerate scoring: `make demo` or `make regenerate-all`.
5. Command to reproduce benchmarks: `make validate-scoring`, `make bench-500`, etc.
6. Command to build the lab batch pack: `make lab-batch-pack`.
7. Where to find evidence certificates, scores, and manifests.
8. How to verify data integrity (SHA-256 hashes).
9. Citation instructions and license.

---

## 12. Preprint / Publication Preparation

- [ ] Methods section drafted from pipeline documentation.
- [ ] Benchmark table prepared from METRICS_CURRENT.md.
- [ ] Honest limitations section (charge-domination, no wet-lab data, simulation modules experimental).
- [ ] Negative result section (all negative findings from Phase 3).
- [ ] Author contributions and acknowledgments.
- [ ] Data and code availability statement.
- [ ] Competing interests declaration.
- [ ] Pre-registration DOIs or timestamps for all locked plans.

---

## Related Documents

- `docs/RELEASE_CHECKLIST.md` — General release process.
- `docs/CLAIM_REVIEW_CHECKLIST.md` — Claim verification before publication.
- `docs/DATA_GOVERNANCE.md` — Data licensing and redistribution policy.
- `docs/ARTIFACT_VERSIONING.md` — Versioning scheme for pipeline outputs.
- `docs/MODEL_CARD_TEMPLATE.md` — Model card format for released scorers.
- `docs/TRUST_CENTER.md` — Trust and safety documentation hub.
