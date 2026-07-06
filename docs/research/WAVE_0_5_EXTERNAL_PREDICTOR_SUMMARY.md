# Wave 0.5 External Predictor Summary

> **Disclaimer:** All values are computational predictions. No antimicrobial activity
> has been demonstrated in vitro or in vivo. Wet-lab validation by qualified
> collaborators is required before any biological claim.
> AntiCP 2.0 predicts anticancer peptides (ACPs), NOT AMP activity.
> HemoFinder predicts hemolysis risk, NOT antimicrobial activity.

Generated: 2026-06-29
Updated: 2026-07-02
Status: **HISTORICAL TEMPLATE ONLY — retained as the pre-submission plan**

---

## Purpose

This document describes the original pre-submission external predictor plan for the
Wave 0.5 shortlist (60 candidates across 10 new seed families). It is preserved as
historical process context, not as the current result state.

The external screen was completed later and the authoritative current-state summary
now lives in [`METRICS_CURRENT.md`](../evidence/METRICS_CURRENT.md)
and [`ROADMAP.md`](research/ROADMAP.md).

---

## Shortlist Summary

| Stat | Value |
|---|---|
| Total shortlisted candidates | 60 |
| New seed families | 10 (SEED-010 through SEED-019) |
| PASS (standard) | 58 |
| PASS_HIGH_UPSIDE | 2 |
| Internal safety ≥ 0.90 (LIKELY_LOW_RISK) | see wave0_5_safety_consensus.csv |

---

## Predictor Stack

### Activity Predictors (4 external)

| Tool | Method | Positive Label | URL |
|---|---|---|---|
| CAMPR4 | SVM + RF + ANN + DT ensemble | AMP | http://www.camp3.bicnirrh.res.in/predict.php |
| AMPScanner v2.0 | LSTM (deep learning) | Antimicrobial | https://www.dveltri.com/ascan/v2/ascan.html |
| Macrel | Random Forest (22 physico + 8 structural features) | AMP (is_AMP=True) | https://big-data-biology.org/software/macrel |
| AMPActiPred | Transformer-based | ABP | (submit FASTA per instructions) |

**IMPORTANT:** Use the Macrel web server, NOT the local CLI (v1.6.0 has a known ONNX bug
that classifies all sequences as NAMP — see existing checklist).

### Safety / Off-Target Predictors (3 external)

| Tool | Predicts | Positive = Risk | URL |
|---|---|---|---|
| HemoFinder | Hemolysis probability | HIGH = hemolytic | (submit sequences) |
| AntiCP 2.0 | Anticancer peptide (ACP) likelihood | ACP+ = off-target risk | https://webs.iiitd.edu.in/raghava/anticp2/ |
| Macrel hemolysis | Hemolytic probability | > 0.5 = flag | same as activity Macrel |

**CRITICAL INTERPRETATION RULE:**
- AntiCP 2.0 is NOT an AMP predictor. A positive AntiCP call means ACP-like / cytotoxic risk.
- Do NOT count AntiCP as activity support.
- Macrel has two roles: activity signal AND hemolysis safety signal.

---

## Activity Consensus Rules

```
STRONG_ACTIVITY  = ≥ 3 positive votes from 4 external activity predictors
MODERATE_ACTIVITY = 2 positive votes
WEAK_ACTIVITY    = ≤ 1 positive vote
```

Target: ≥ 20 candidates with STRONG_ACTIVITY.
Target: ≥ 10 candidates with STRONG_ACTIVITY + LOW/MIXED_RISK safety.

---

## Safety Risk Rules

```
LOW_RISK   = HemoFinder LOW + AntiCP non-ACP + Macrel hemolysis NEGATIVE
MIXED_RISK = exactly one safety warning (any of the above flags)
HIGH_RISK  = two or more safety warnings
```

---

## Internal Score Pre-Screening (Available Now)

Pending external results, the internal OpenAMP safety scores provide a first estimate:

| Internal Safety Band | Interpretation | Candidate Count |
|---|---|---|
| ≥ 0.90 | LIKELY_LOW_RISK | ~30 |
| 0.75–0.90 | UNCERTAIN (need HemoFinder/AntiCP) | ~30 |
| < 0.75 | Not shortlisted (filtered out in Phase 4) | — |

No candidate in the Wave 0.5 shortlist has the very-high-Trp aromatic signature
of SEED-008 (which carried explicit HIGH hemolysis risk). The shortlist does NOT
contain SEED-008 variants.

SEED-016 (RRWK dual-Trp) contains 2 Trp residues (vs 3-4 in SEED-008). Internal
safety scores 0.94 suggest moderate risk — HemoFinder is recommended to confirm.

SEED-012_VAR_001 (GKLKKLVKKLLK) and SEED-012_VAR_006 (GKLKKLVKKFLK) are labeled
PASS_HIGH_UPSIDE because their internal safety = 0.75 (borderline). HemoFinder
confirmation required before synthesis.

---

## Historical Submission Procedure

1. Export `outputs/wave0_5_internal_shortlist.csv` → extract sequences column
2. Create FASTA file from all 60 sequences
3. Submit to each tool's web interface (see URLs above)
4. Record Y/N (or probability score) per candidate per tool
5. Fill in `outputs/wave0_5_external_predict_results.csv`
6. Run `make wave0-5-fill-external` to derive the Wave 0.5 result files when
   `outputs/wave05_combined_consensus.csv` is available in the local checkout.

---

## Historical Artifact Expectations

| File | Status |
|---|---|
| `outputs/wave0_5_external_predict_results.csv` | Generated only after running `make wave0-5-fill-external` with local source data |
| `outputs/wave0_5_external_consensus.csv` | Generated only after running `make wave0-5-fill-external` with local source data |
| `outputs/wave0_5_safety_consensus.csv` | Generated only after running `make wave0-5-fill-external` with local source data |

---

## Phase 5 Acceptance Criteria (after filling in)

When results are filled in, the shortlist must contain:

```
≥ 20 candidates with STRONG_ACTIVITY
≥ 10 candidates with STRONG_ACTIVITY + LOW/MIXED_RISK
≥ 6 candidates from new seed families with STRONG_ACTIVITY
```

If not achieved, return to Phase 3 and generate additional candidates.

---

## See Also

- `outputs/wave0_5_internal_shortlist.csv` — 60 candidates with internal scores
- `docs/research/WAVE_0_5_BASELINE.md` — Wave 0 panel baseline
- `docs/evidence/EXTERNAL_PREDICTOR_CONSENSUS.md` — Wave 0 consensus (same tool stack)
