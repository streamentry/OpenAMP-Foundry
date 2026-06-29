# Pipeline Decision Rules

> **Purpose:** Pre-registered pass/fail gates for each stage of the OpenAMP Foundry
> pipeline. Thresholds are hardcoded (see `src/openamp_foundry/gates/gate_checker.py`)
> to prevent cherry-picking after inspecting results.
>
> **Locked:** 2026-06-29 (Sprint 5)

---

## Gate 1 — AUROC Benchmark

| Field | Value |
|-------|-------|
| Threshold | AUROC ≥ **0.70** |
| Measure | Pipeline AUROC on expanded 95+96 benchmark |
| Config | `configs/pipeline.yaml` |
| Action | If FAIL: Do not proceed to synthesis |

## Gate 2 — Leakage Guard

| Field | Value |
|-------|-------|
| Threshold | Recall@43 < **0.60** |
| Measure | Fraction of positives recovered in top 43 ranked |
| Rationale | Recall@43 > 0.60 suggests near-duplicate memorisation |
| Action | If FAIL: Investigate reference-set contamination |

## Gate 3 — Model Disagreement

| Field | Value |
|-------|-------|
| Threshold | Top-3 candidate |activity − boman_activity| < **0.45** |
| Measure | Absolute difference between two independent scorers |
| Config | `configs/pipeline.yaml`, `configs/phase3.yaml` |
| Action | If FAIL: Review scorer weights or threshold |

## Gate 4 — Top-10 Recall

| Field | Value |
|-------|-------|
| Threshold | Recall@10 > **0.0** |
| Measure | At least 1 positive in top 10 ranked candidates |
| Action | If FAIL: Scoring model likely broken |

## Gate 5 — Interpretation

| Field | Value |
|-------|-------|
| Threshold | Benchmark interpretation must be **STRONG** |
| Measure | String match of `interpretation` field |
| Action | If FAIL: Do not proceed |

## Gate 6 — External Predictor Consensus

| Field | Value |
|-------|-------|
| Threshold | ≥3/5 external tools positive |
| Measure | Manual web submission results |
| Status | PENDING (see `outputs/external_predict_checklist.md`) |
| Action | If FAIL: Expert reviewer override required |

## Gate 7 — Human Expert Review

| Field | Value |
|-------|-------|
| Threshold | Expert reviewer APPROVE or CONDITIONAL |
| Measure | Completed reviewer questionnaire |
| Status | PENDING (see `outputs/questionnaire/`) |
| Action | If REJECT: Exclude from synthesis |

---

## CLI Usage

```bash
# Check all gates:
openamp-foundry gate-check \
    --validation-json outputs/validate_scoring_report.json

# Check specific gate:
openamp-foundry gate-check --gate 1 \
    --validation-json outputs/validate_scoring_report.json
```

## Hardcoding Rule

All gate thresholds in `gates/gate_checker.py` are **hardcoded** (not configurable
via YAML). To change a threshold: modify source code, commit, and create a new release.
This prevents silent threshold drift that could mask performance regression.

---

## Wave 0.5 Gates (Scaffold Diversification)

Added 2026-06-29. See `src/openamp_foundry/gates/wave0_5_gate_checker.py`.

### Gate W0.5-1 — Family Diversity

| Field | Value |
|-------|-------|
| Threshold | ≥8 independent scaffold families in final panel |
| Current | 13 families |
| Status | PASS |

### Gate W0.5-2 — Family Redundancy

| Field | Value |
|-------|-------|
| Threshold | No lead family contributes more than 2 lead candidates |
| Current | Max 2 per family enforced |
| Status | PASS |

### Gate W0.5-3 — Activity Consensus

| Field | Value |
|-------|-------|
| Threshold | ≥70% of lead candidates have STRONG_ACTIVITY (≥3/3 external predictors; CAMPR4 not submitted) |
| Current | 52/60 STRONG_ACTIVITY (87%) — AMPScanner 59/60, Macrel 52/60, AMPActiPred 60/60 |
| Status | **PASS** |

### Gate W0.5-4 — Safety Annotation

| Field | Value |
|-------|-------|
| Threshold | 100% of candidates have HemoFinder and AntiCP annotations |
| Current | 60/60 annotated: HemoFinder LOW 40/60, HIGH 20/60; AntiCP Non-AntiCP 4/60, AntiCP 56/60 |
| Safety concern | 56/60 AntiCP-positive (amphipathic helix pattern triggers ACP prediction); Wave 0.5b addresses this |
| Status | **PASS** |

### Gate W0.5-5 — Novelty Qualification

| Field | Value |
|-------|-------|
| Threshold | ≥8 candidates are HIGH_CONFIDENCE_NOVEL, RELATED_NOVEL, or CLOSE_RELATIVE (updated after v2 audit) |
| Method | BioPython PairwiseAligner BLOSUM62 local alignment vs 27,234 unique AMPs (APD6+DRAMP+UniProt) |
| v2 result | 19 lead candidates with CLOSE_RELATIVE or better novelty (v1 result: 53/60, now corrected) |
| v1 caveat | v1 used Levenshtein/max-length vs 72 refs — undercounted similarity, overstated novelty |
| Status | **PASS** |

### Gate W0.5-6 — Control Integrity

| Field | Value |
|-------|-------|
| Threshold | Known/control candidates labeled CONTROL or SAR_CONTROL, not LEAD |
| Current | SEED-001 → POSITIVE_CONTROL; SEED-003 → SAR_CONTROL; verified |
| Status | PASS |

### Gate W0.5-7 — Claim Safety

| Field | Value |
|-------|-------|
| Threshold | No unsupported wet-lab, drug, antibiotic, cure, or clinical claims in docs |
| Current | All docs include required disclaimer |
| Status | PASS |
