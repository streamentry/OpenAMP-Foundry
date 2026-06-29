# Full Novelty Audit

> **Generated:** 2026-06-29T06:43:49Z
> **Panel:** 20 candidates | **Reference set:** 120 sequences
> **Thresholds:** EXACT=1.0, KNOWN_VARIANT≥0.70, CLOSE_RELATIVE≥0.50, HIGH_CONFIDENCE_NOVEL≥0.60 novelty

---

## Summary

| Category | Count | Publication strategy |
|----------|:-----:|---------------------|
| **HIGH_CONFIDENCE_NOVEL** | 13 | Primary novelty claim — publish as novel family |
| **NOVEL** | 3 | Primary novelty claim — publish as novel family |
| **CLOSE_RELATIVE** | 1 | Conditional — requires mechanism distinction |
| **KNOWN_VARIANT** | 3 | SAR/control only — not novelty-claimable |

**Reference hit frequency (best-match database):**

- REF-TMPG-001 (temporin_G): 4x
- REF-RRW-001 (tachyplesin_like): 4x
- REF-KWK-001 (template_seed_1): 2x
- REF-DROS-001 (drosocin): 1x
- REF-TRP-001 (tryptophan_rich_cathelicidin): 1x
- REF-PYR-001 (pyrrhocoricin): 1x
- REF-BUF-002 (buforin_ii): 1x
- REF-SCO-001 (scorpion_isct): 1x
- REF-LL37-002 (cathelicidin_ll37_fragment): 1x
- REF-BP1-001 (bp100_designed): 1x
- REF-RLK-001 (cationic_tryptophan): 1x
- REF-JAP1-001 (japonicin): 1x
- REF-IND-002 (indolicidin_analog): 1x

## Per-Candidate Classification

| Rank | Candidate | Seed | Ensemble | Novelty | Category | Best reference | Layer |
|:----:|-----------|:----:|:--------:|:-------:|:--------:|----------------|:----:|
| 1 | SEED-009_VAR_033 | SEED-009 | 0.807 | 0.632 | [HC] HIGH_CONFIDENCE_NOVEL | drosocin | 5 |
| 2 | SEED-009_VAR_027 | SEED-009 | 0.808 | 0.692 | [HC] HIGH_CONFIDENCE_NOVEL | tryptophan_rich_cathelicidin | 5 |
| 3 | SEED-007_VAR_009 | SEED-007 | 0.849 | 0.643 | [HC] HIGH_CONFIDENCE_NOVEL | temporin_G | 5 |
| 4 | SEED-007_VAR_001 | SEED-007 | 0.824 | 0.571 | [NV] NOVEL | temporin_G | 4 |
| 5 | SEED-007_VAR_018 | SEED-007 | 0.815 | 0.571 | [NV] NOVEL | temporin_G | 4 |
| 6 | SEED-009_VAR_039 | SEED-009 | 0.796 | 0.650 | [HC] HIGH_CONFIDENCE_NOVEL | pyrrhocoricin | 5 |
| 7 | SEED-009_VAR_017 | SEED-009 | 0.798 | 0.647 | [HC] HIGH_CONFIDENCE_NOVEL | buforin_ii | 5 |
| 8 | SEED-007_VAR_035 | SEED-007 | 0.806 | 0.571 | [NV] NOVEL | temporin_G | 4 |
| 9 | SEED-006_VAR_059 | SEED-006 | 0.821 | 0.643 | [HC] HIGH_CONFIDENCE_NOVEL | tachyplesin_like | 5 |
| 10 | SEED-006_VAR_071 | SEED-006 | 0.828 | 0.643 | [HC] HIGH_CONFIDENCE_NOVEL | scorpion_isct | 5 |
| 11 | SEED-006_VAR_062 | SEED-006 | 0.841 | 0.643 | [HC] HIGH_CONFIDENCE_NOVEL | cathelicidin_ll37_fragment | 5 |
| 12 | SEED-006_VAR_006 | SEED-006 | 0.812 | 0.643 | [HC] HIGH_CONFIDENCE_NOVEL | bp100_designed | 5 |
| 13 | SEED-008_VAR_032 | SEED-008 | 0.857 | 0.692 | [HC] HIGH_CONFIDENCE_NOVEL | tachyplesin_like | 5 |
| 14 | SEED-008_VAR_009 | SEED-008 | 0.849 | 0.692 | [HC] HIGH_CONFIDENCE_NOVEL | cationic_tryptophan | 5 |
| 15 | SEED-008_VAR_019 | SEED-008 | 0.845 | 0.684 | [HC] HIGH_CONFIDENCE_NOVEL | japonicin | 5 |
| 16 | SEED-003_VAR_017 | SEED-003 | 0.816 | 0.182 | [KV] KNOWN_VARIANT | tachyplesin_like | 2 |
| 17 | SEED-003_VAR_012 | SEED-003 | 0.807 | 0.182 | [KV] KNOWN_VARIANT | tachyplesin_like | 2 |
| 18 | SEED-008_VAR_044 | SEED-008 | 0.832 | 0.600 | [HC] HIGH_CONFIDENCE_NOVEL | indolicidin_analog | 5 |
| 19 | SEED-005_VAR_019 | SEED-005 | 0.808 | 0.400 | [CR] CLOSE_RELATIVE | template_seed_1 | 3 |
| 20 | SEED-001_VAR_064 | SEED-001 | 0.802 | 0.133 | [KV] KNOWN_VARIANT | template_seed_1 | 2 |

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
| **1** | HIGH_CONFIDENCE_NOVEL (< 40% sim, no motif concern) | 13 | Primary breakthrough targets. Lead publication. |
| **2** | NOVEL (< 50% sim) | 3 | Claim as novel family. Verify mechanism unique. |
| **3** | CLOSE_RELATIVE (50-70% sim) | 1 | Conditional — require mechanism distinction for novelty claim. |
| **4** | KNOWN_VARIANT (≥70% sim) | 3 | Exclude from novelty claims. Keep as SAR/assay controls. |
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
