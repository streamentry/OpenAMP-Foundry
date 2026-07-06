# Wave 2 Active-Learning Plan

**Version:** 1.0
**Date:** 2026-06-28
**Status:** Pre-registered strategy — locked before Wave 1 assay results are analysed

---

## Purpose

This document pre-specifies the Wave 2 strategy for each possible Wave 1 outcome. Pre-specifying
Wave 2 before seeing Wave 1 results prevents outcome-dependent strategy changes that would
invalidate the iterative learning loop.

> **Mandatory:** Read Wave 1 results BEFORE opening this document further than the decision tree
> below. Do not change any Wave 2 parameters based on Wave 1 outcomes that are not in scope here.

---

## Wave 1 → Wave 2 Decision Tree

### Scenario A: 0 hits (all MIC > 128 µg/mL across all organisms)

**Interpretation:** Either the scoring model is miscalibrated for this peptide series, or the
target organisms are resistant to all scaffold families tested.

**Wave 2 actions:**
1. Run `make validate-scoring` on a dataset that includes Wave 1 inactive candidates as negatives
   → AUROC drop > 0.05 indicates the scoring model needs recalibration
2. Add D-amino acid variants of the 3 highest-scoring Wave 1 candidates (scaffold rescue attempt)
3. Add 2 new seed families from outside the current 10 — prioritise:
   - β-sheet forming scaffold (protegrin-type, without Cys): e.g. VDKPPYLPRPRPPHPRI
   - Arginine-rich non-amphipathic scaffold: e.g. RRIRPRPPRLPRPRPRR
4. Publish negative result with full pipeline transparency

**Do NOT:** Synthethise additional variants from the same 10 seed families without mechanistic
rationale. Correlation between near-seed variants means new variants from the same seeds add
minimal new information.

---

### Scenario B: ≥1 active (MIC ≤ 32 µg/mL) but 0 selective (all TI < 5)

**Interpretation:** The pipeline has identified biologically active scaffolds but they are too
toxic for mammalian cells. This is a selectivity problem, not an activity problem.

**Wave 2 strategy: selectivity improvement**

For each active-but-toxic candidate:

| Modification | Goal | How |
|-------------|------|-----|
| C-terminal truncation (−2 to −4 residues) | Reduce hydrophobic tail | Resynthesise truncated variant |
| Hydrophobic → polar substitution (L→S, F→Y) at C-terminus | Reduce amphipathicity | Generator: conservative substitution |
| D-amino acid at critical Trp/Phe position | Reduce membrane affinity | Manual design |
| Introduce Gly/Pro helix-breaker | Disrupt continuous hydrophobic face | Generator: Gly-insertion |

Run modified variants through `make score` and filter by:
- selectivity_proxy > 0.60 (stricter than 0.50)
- safety_score > 0.65
- activity_score > 0.60

Target: 10 selectivity-improved variants from the 3 most active Wave 1 scaffolds.

---

### Scenario C: ≥1 hit (MIC ≤ 32 µg/mL AND TI ≥ 10) — primary success case

**Interpretation:** The pipeline has identified at least one therapeutically relevant AMP candidate.

**Wave 2 strategy: hit confirmation + serum stability**

#### C1 — Hit confirmation (priority 1)

Re-test all confirmed hits (Scenario C candidates) in at least one additional lab for
independent replication. Required for publication and to rule out assay artefacts.

**Target MIC for high-impact classification:**

| MIC range | Classification |
|-----------|---------------|
| ≤ 4 µg/mL | Outstanding — major publication target |
| 4–16 µg/mL | Strong — publishable with selectivity evidence |
| 16–32 µg/mL | Moderate — publishable if spectrum is broad or scaffold is genuinely novel |

#### C2 — D-amino acid variants (priority 2)

For each Scenario C hit, generate D-amino acid variants at proteolytic sites (machine-readable
guidance in synthesis_checklist.md):

- D-Lys at each trypsin K site
- D-Arg at each trypsin R site
- D-Trp at first tryptophan if present (chymotrypsin site)

Expected serum stability gain: 3–10× (from t½ ~0.5 h → ~2–5 h).

Run D-variants through `make score`. Expected activity retention: 60–80% of parent activity
(some loss from reduced amphipathicity is acceptable if stability is gained).

#### C3 — MDR strain panel (priority 3)

Test confirmed hits against:

| Organism | Strain | Rationale |
|----------|--------|-----------|
| MRSA | USA300 (ATCC BAA-1556) | Most clinically relevant community-acquired MRSA strain |
| K. pneumoniae NDM-1 | ATCC BAA-2146 | NDM-1 carbapenemase-producing; carbapenem-resistant (not merely ESBL) |
| A. baumannii MDR | ATCC BAA-1710 | Clinical MDR isolate from ESKAPE panel; multi-drug resistant |

> **Note:** ATCC 19606 is A. baumannii's susceptible reference strain — do NOT use it for MDR
> testing. ATCC BAA-1710 is the correct clinical MDR representative.

Expected activity: AMPs from the current scaffold classes are typically more active against
MRSA than Gram-negative MDR strains. SEED-009 (Bac2A, proline-rich) may have better
Gram-negative activity than the membrane-disrupting seeds.

> **Scoring note for SEED-008 (puroindoline-a, Trp-rich):** SEED-008 candidates show model
> disagreement ~0.37 due to mechanistic divergence between the two scorers, NOT prediction
> uncertainty. The Boman scale (W = −3.398 kcal/mol) penalises Trp as highly hydrophobic and
> protein-binding, systematically under-ranking Trp-rich AMPs. The Wimley-White interfacial
> scale (W = −1.85 kcal/mol) correctly models Trp's interfacial membrane-insertion mechanism.
> PR #65 added a 1.5× Trp aromatic bonus to partially compensate. If SEED-008 variants are
> active in Wave 1, Wave 2 should expand the Trp-rich scaffold with confidence — disagreement
> is a mechanistic marker, not a model failure.

#### C4 — Mechanism confirmation (priority 4, for top 1–2 hits only)

If budget permits, run one mechanistic assay:
- **Membrane potential assay** (DiSC3 dye): distinguishes pore-forming from carpet mechanism
- **DNA/RNA binding assay**: confirms intracellular target for SEED-009 variants
- **Electron microscopy**: gold standard for membrane disruption confirmation

---

## Wave 2 Candidate Generation

To generate Wave 2 candidates from Wave 1 hits, run:

```bash
# Replace SEED-00X_VAR_NNN with the actual Wave 1 hit IDs
make generate SEED_OVERRIDE=SEED-00X_VAR_NNN

# Score and filter
make score
make pilot
```

For D-amino acid variant generation, the synthesis_checklist.md generated by `make synthesis-order`
already contains D-amino substitution instructions per candidate. Convert these to new seed
sequences manually and re-run the pipeline.

---

## Wave 2 Resource Budget (pre-registered)

| Scenario | Wave 2 candidates | Target cost |
|----------|-----------------|------------|
| A (all inactive) | 10–12 (new scaffold variants) | ~$2,000–3,000 synthesis |
| B (active, toxic) | 10 (selectivity-improved) | ~$2,000 synthesis |
| C (confirmed hits) | 5–10 D-amino + 3–5 MDR tests | ~$3,000–5,000 synthesis + assay |

---

## Learning Loop — What Wave 1 Teaches Us

Regardless of Wave 1 outcome, extract these pipeline calibration signals:

| Signal | How to extract | What to update |
|--------|---------------|----------------|
| Per-seed hit rate | Count hits per seed family | Seed prior probability in DISCOVERY_PREDICTION.md |
| Score correlation with MIC | Pearson r(ensemble_score, 1/MIC) | Pipeline AUROC calibration note |
| Synthesis failures | Count by flagged risk | Synthesis feasibility scoring thresholds |
| Selectivity proxy accuracy | Compare proxy < 0.5 to observed TI < 5 | Selectivity proxy weight in pilot_priority |
| AUPRC on expanded dataset | Add Wave 1 inactive as negatives | METHODS.md benchmark section |

Archive these signals in `outputs/wave1_learning.md` within 4 weeks of receiving all results.

---

## References

- Zasloff M (2002) Antimicrobial peptides of multicellular organisms. Nature 415:389–395
- Melo MN et al. (2009) Antimicrobial peptides: linking partition, activity and high membrane-bound concentrations. Nat Rev Microbiol 7:245–250
- Guinas ML et al. (2019) Cecropin A–melittin hybrid peptides: A review on their ability to destabilize biological membranes. Curr Protein Pept Sci 20:860–870
- Chung PY et al. (2017) Proline-rich antimicrobial peptides. Mini Rev Med Chem 17:1484–1494
