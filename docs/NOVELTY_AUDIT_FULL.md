# Full Novelty Audit

> **Generated:** 2026-06-29T03:15:59Z
> **Panel:** 20 candidates | **Reference set:** 120 sequences
> **Thresholds:** EXACT=1.0, KNOWN_VARIANT≥0.70, CLOSE_RELATIVE≥0.50, HIGH_CONFIDENCE_NOVEL≥0.60 novelty

---

## Summary

| Category | Count | Publication strategy |
|----------|:-----:|---------------------|
| **HIGH_CONFIDENCE_NOVEL** | 20 | Primary novelty claim — publish as novel family |

**Reference hit frequency (best-match database):**

- REF-TN1-001 (tenecin_1): 20x

## Per-Candidate Classification

| Rank | Candidate | Seed | Ensemble | Novelty | Category | Best reference | Layer |
|:----:|-----------|:----:|:--------:|:-------:|:--------:|----------------|:----:|
| 1 | SEED-009_VAR_033 | SEED-009 | 0.807 | 0.862 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 2 | SEED-009_VAR_027 | SEED-009 | 0.808 | 0.828 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 3 | SEED-007_VAR_009 | SEED-007 | 0.849 | 0.897 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 4 | SEED-007_VAR_001 | SEED-007 | 0.824 | 0.897 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 5 | SEED-007_VAR_018 | SEED-007 | 0.815 | 0.862 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 6 | SEED-009_VAR_039 | SEED-009 | 0.796 | 0.862 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 7 | SEED-009_VAR_017 | SEED-009 | 0.798 | 0.862 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 8 | SEED-007_VAR_035 | SEED-007 | 0.806 | 0.897 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 9 | SEED-006_VAR_059 | SEED-006 | 0.821 | 0.931 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 10 | SEED-006_VAR_071 | SEED-006 | 0.828 | 0.931 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 11 | SEED-006_VAR_062 | SEED-006 | 0.841 | 0.828 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 12 | SEED-006_VAR_006 | SEED-006 | 0.812 | 0.897 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 13 | SEED-008_VAR_032 | SEED-008 | 0.857 | 0.897 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 14 | SEED-008_VAR_009 | SEED-008 | 0.849 | 0.897 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 15 | SEED-008_VAR_019 | SEED-008 | 0.845 | 0.862 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 16 | SEED-003_VAR_017 | SEED-003 | 0.816 | 0.897 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 17 | SEED-003_VAR_012 | SEED-003 | 0.807 | 0.862 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 18 | SEED-008_VAR_044 | SEED-008 | 0.832 | 0.897 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 19 | SEED-005_VAR_019 | SEED-005 | 0.808 | 0.828 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |
| 20 | SEED-001_VAR_064 | SEED-001 | 0.802 | 0.897 | [HC] HIGH_CONFIDENCE_NOVEL | tenecin_1 | 5 |

## Family-Level Notes

### SEED-001 (1 candidates)

Magainin-1 derivative. Near-identical to known template. Positive control only.

### SEED-003 (2 candidates)

Cationic Trp helix. KNOWN_VARIANT → tachyplesin-like (Tam 2002). Keep as SAR control.

### SEED-005 (1 candidates)

Cecropin-magainin hybrid. CLOSE_RELATIVE to template_seed_1. Conditional novelty.

### SEED-006 (4 candidates)

Mastoparan-X wasp venom. Genuinely novel scaffold. Primary breakthrough target.

### SEED-007 (4 candidates)

Bombolitin-II bumblebee venom. Highest-novelty family in panel.

### SEED-008 (4 candidates)

Puroindoline-a Trp-rich domain. Novel mechanism (indole intercalation).

### SEED-009 (4 candidates)

Bac2A proline-rich intracellular. Novel mechanism (DnaK binding).


## Priority for Novelty Claims

| Tier | Category | Candidates | Recommendation |
|:----:|----------|:----------:|----------------|
| **1** | HIGH_CONFIDENCE_NOVEL (< 40% sim, no motif concern) | 20 | Primary breakthrough targets. Lead publication. |
| **2** | NOVEL (< 50% sim) | 0 | Claim as novel family. Verify mechanism unique. |
| **3** | CLOSE_RELATIVE (50-70% sim) | 0 | Conditional — require mechanism distinction for novelty claim. |
| **4** | KNOWN_VARIANT (≥70% sim) | 0 | Exclude from novelty claims. Keep as SAR/assay controls. |
| **5** | EXACT_MATCH (100%) | 0 | Exclude. Positive control only. |

## Caveats

1. **Reference database:** 120 sequences (unified AMP library). This is not APD3 (3,000+) or DRAMP (19,000+).
2. **Similarity metric:** Levenshtein edit distance. Does not capture structural or functional similarity.
3. **Patent check:** Not included here — see `outputs/patent_risk_screen.csv` for manual check.
4. **Competitor sequences:** Not included here — see `docs/COMPETITOR_NON_OVERLAP_REPORT.md`.
5. **External predictors:** Not included — consensus gate requires ≥3/5 tools positive.

## References

- Curated reference set: `examples/known_reference/amp_curated_references.csv`
- Expanded AMP set: `examples/validation/known_amps.csv`
- Levenshtein distance: `scoring/novelty.py`
- Tool: `scripts/run_novelty_audit.py`
