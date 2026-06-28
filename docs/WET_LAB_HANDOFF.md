# Wet-Lab Handoff Guide

**Version:** 0.1.0  
**Status:** Working draft for expert review before synthesis ordering.

---

## Purpose

This document translates pipeline output scores into synthesis and assay decisions for wet-lab
scientists. Every nominated candidate has a JSON evidence certificate and a pre-synthesis QC
report. This guide explains what each number means, what action it recommends, and what to do
when fewer candidates pass the filters than expected.

---

## Score Reference Table

All scores are on a **[0, 1] scale**. Higher is better (except `disagreement`, which is lower is better).

| Score key | What it measures | Low (< 0.4) | Medium (0.4–0.7) | High (> 0.7) |
|-----------|-----------------|------------|-----------------|-------------|
| `activity` | Physicochemical similarity to known AMPs (charge, hydrophobicity, amphipathicity) | Unlikely AMP-like | Possible candidate | Strong AMP signature |
| `safety` | Absence of hemolysis risk, toxic motif similarity, mammalian membrane affinity | High host-cell risk — exclude | Monitor carefully | Safe to proceed |
| `synthesis` | SPPS synthesis feasibility (length, Cys content, repeat runs) | Difficult / high failure risk | Moderate; check QC report | Straightforward synthesis |
| `novelty` | Sequence distance from known AMP references | Near-duplicate of known AMP | Moderate novelty | New structural territory |
| `ensemble` | Weighted combination of above four scores | Below priority threshold | Borderline | Priority candidate |
| `disagreement` | |activity_likeness − boman_activity| — scorer consensus | High consensus (good) | Some divergence | Low consensus — treat cautiously |

### Recommended Action by Ensemble Score

| Ensemble range | Recommendation |
|---------------|---------------|
| ≥ 0.70 | **Synthesise** — priority candidate |
| 0.55–0.69 | **Conditional synthesis** — review QC flags first |
| 0.40–0.54 | **Expert review required** — only if budget allows |
| < 0.40 | **Do not synthesise** — fails pipeline threshold |

---

## Selection Thresholds

The pipeline uses four gates before a candidate is marked `selected: true`.

| Gate | `pipeline.yaml` | `phase3.yaml` | Why |
|------|----------------|--------------|-----|
| `min_novelty` | ≥ 0.20 | ≥ 0.05 | Near-duplicates waste budget on already-known peptides |
| `max_safety_risk` → min safety | ≤ 0.70 → safety ≥ 0.30 | ≤ 0.40 → safety ≥ 0.60 | Phase 3 is the final synthesis batch — only clean candidates |
| `max_disagreement` | ≤ 0.40 | ≤ 0.40 | When physchem and Boman scoring diverge > threshold, both models are guessing. Both configs use 0.40 — Trp-rich scaffolds (SEED-008) show disagreement ~0.37 due to mechanism divergence (interfacial insertion vs Boman electrostatic scale), not uncertainty |
| Sequence validity | canonical AA only | same | Non-canonical residues are disqualified |

A candidate must pass **all four gates** to be nominated. Failing any single gate → `selected: false`.

---

## Pre-Synthesis QC Report Interpretation

Run `make presynth-qc` (or `openamp-foundry presynth-qc --panel-csv <file>`) on the final panel
before ordering. The report flags:

| Flag | Risk | Action |
|------|------|--------|
| `CYSTEINE×N` | Disulfide formation, oxidation during storage | Order under inert atmosphere; store in N₂; check purity pre-assay |
| `MET×N` | Met oxidation to sulfoxide in air | Order with >95% purity; store at −80°C; re-check purity on thaw |
| `HYDROPHOBIC_RUN (XXXX)` | Aggregation; poor aqueous solubility | Test solubility at 1 mM in PBS before assay; add 0.1% DMSO if needed |
| `TRYPSIN_SITES×N` (N > 2) | Serum degradation < 2h | Use serum-free media for initial MIC; add protease inhibitors if needed |
| `WAVE2_D_AMINO` | Wave 2 D-amino acid sites identified | See `wave2_d_substitutions` field — substitute D-Lys or D-Arg at listed positions in Wave 2 synthesis to extend serum t½ by 3–10× |
| `N_ACETYLATION_RECOMMENDED` | N-terminal aminopeptidase exposure | **Request "N-terminal acetylation (Ac-)"** in synthesis order — zero cost, blocks aminopeptidase entry |
| `DEAMIDATION_RISK` | Asn/Gln (N/Q) → Asp/Glu conversion via succinimide at pH > 7.5 (NG, NS, QG, QS motifs) | Use pH 5–6 lyophilization buffer; reconstitute in pH 7.0 just before assay; avoid >24h storage at room temperature |
| `ISOMERIZATION_RISK` | Asp (D) → β-Asp backbone rearrangement (DG, DS motifs); changes peptide geometry | Store lyophilized at −20°C; verify HPLC purity after reconstitution to detect β-Asp peaks (~+14 min retention shift) |
| `TRP_PHOTOLABILITY (N Trp)` | Trp photooxidizes to kynurenine under ambient/UV light (≥3 Trp residues) | Store in amber or foil-wrapped vials; handle under red/dim light; use aliquots; complete assay within 2h of thaw. Check A280 before and after assay for degradation. |
| `LOW_CHARGE` | Reduced membrane affinity | Lower expected potency; may need higher test concentrations |
| `LONG_PEPTIDE (>30aa)` | SPPS yield risk | Expect lower crude purity; order extra crude for purification |
| `C_AMIDATION_RECOMMENDED` | C-terminal COOH reduces charge and serum stability | **Request "C-terminal amide (CONH₂)"** in synthesis order form — adds ~+0.7 charge, improves stability at zero extra cost |

### Synthesis Difficulty Rating

| Rating | Meaning | Action |
|--------|---------|--------|
| LOW | ≤ 0 flags | Standard SPPS protocol; Fmoc chemistry |
| MODERATE | 1–2 flags | Standard protocol + address specific flags above |
| HIGH | ≥ 3 flags | Discuss with peptide synthesis vendor; consider Boc chemistry or ligation |

---

## Assay Recommendations

### Initial Screen (MIC Assay)

**Reference strain panel (Wave 1 minimum):**

| Organism | ATCC strain | Gram | Rationale |
|----------|-------------|------|-----------|
| *E. coli* | ATCC 25922 | − | Gram-negative standard; reference for all AMP comparisons |
| *S. aureus* | ATCC 29213 | + | Gram-positive standard; reference for all AMP comparisons |

**MDR expansion (Wave 1 recommended — adds publication significance):**

| Organism | Strain | Resistance phenotype | Why include |
|----------|--------|----------------------|-------------|
| *S. aureus* | USA300 | MRSA (methicillin-resistant) | Clinically prevalent; any hit is immediately publishable |
| *E. coli* | ST131 (ATCC BAA-2469) | MDR (CTX-M ESBL) | Most prevalent MDR Gram-negative globally |
| *K. pneumoniae* | ATCC BAA-1705 | KPC (carbapenem-resistant) | Highest-priority WHO critical pathogen |

Including MDR strains adds only ~3× material cost but increases publication impact substantially.
Any candidate with MIC ≤ 8 μg/mL against MRSA or KPC-KP qualifies as clinically significant.

- **Growth medium:** MHB (Mueller-Hinton Broth), cation-adjusted
- **Inoculum:** ~5×10⁵ CFU/mL (CLSI standard)
- **Concentration range:** 1–128 μg/mL (2-fold serial dilutions)
- **Replicates:** ≥ 3 biological replicates per candidate
- **Positive control:** Colistin (Gram-negative), Oxacillin (Gram-positive)
- **Negative control:** Solvent blank matching highest solvent concentration

### Hemolysis Assay (Safety Gate)

Run in parallel with MIC. The `hemolysis_start_conc` field in the presynth QC report gives the
recommended starting concentration based on the computed hydrophobic moment (μH):

| μH range | Starting concentration |
|---------|----------------------|
| ≤ 0.55 | Start at MIC (low risk) |
| > 0.55 and ≤ 0.80 | Start at MIC/3 (moderate risk) |
| > 0.80 | Start at MIC/10 (high risk — very cautious) |

Use human red blood cells (hRBCs) at 0.5% in PBS. Incubate 1h at 37°C. Read at A540.
Hemolysis > 10% at MIC is a fail.

---

## SEED-006 (Mastoparan-X) Special Notes

SEED-006 variants are derived from **Mastoparan-X** (INWKGIAAMAKKLL, Yoshida *et al.* 1990),
a wasp (*Vespa xanthoptera*) venom calmodulin-binding helical peptide. This is structurally
distinct from the other 5 seeds (magainin-like, cecropin-like, tachyplesin-like). 

**Mechanism:** Mastoparan-X inserts into bacterial membranes via a predominantly
**hydrophobic helix insertion** mechanism rather than electrostatic carpet disruption.
It also activates G-proteins and has calmodulin-binding properties.

**Expected activity profile:**
- Gram-positive coverage likely > Gram-negative (small outer membrane)
- May show cooperative ("all-or-nothing") dose-response curves
- Hemolytic risk: moderate (assay at MIC/3 per QC guidance)

**Synthesis guidance:**
- No Cys, no Met → standard Fmoc SPPS, standard storage
- **C-terminal amidation strongly recommended**: SEED-006_VAR_xxx candidates end in LL (hydrophobic),
  neutral C-terminus. Request `CONH₂` to add +0.7 charge and improve serum stability
- SEED-006 variants have 2–3 interior Lys → serum t½ estimated ~2–4 h

**Assay interpretation:**
- If SEED-006 variants are active but SEED-003/005/007/008/009 are not: supports calmodulin-binding
  mechanism; consider calmodulin competition assay to confirm novel mechanism
- High publication value if MIC < 4 μg/mL against MRSA (see MDR panel above)

---

## Serum Stability Model Limitations (SEED-003, SEED-005, SEED-008)

The `serum_stability_score()` function is calibrated for medium-length cationic helices (~18–30 AA).
All 6 pilot panel seed families have model scores below the 0.70 threshold (t½ > 2h gate).
Three families are flagged as borderline or likely model underestimates:

| Scaffold | Pilot score | Issue | Expected actual t½ | Action |
|----------|-------------|-------|-------------------|--------|
| SEED-003 (cationic helix, 11–14 AA) | 0.35–0.38 | Short peptide has fewer cleavage sites than the model's per-length baseline — systematic underestimate | **Likely > model prediction** — Radzishevsky et al. (2007, Nat Biotechnol): short AMPs show 2–5× longer t½ than length-matched controls predict | Do not exclude on serum score alone. Run assay and compare to model |
| SEED-005 (cecropin-magainin hybrid, 14 AA) | 0.449 | Borderline score below 0.50 (t½ > 1h) threshold; only 1 pilot slot — any failure drops this family | ~30 min–1 h by model; no documented correction factor | Prioritise in early serum screen; D-Lys Wave 2 plan ready if needed |
| SEED-008 (puroindoline-a, Trp-rich) | 0.45 | Indole ring bulk reduces chymotrypsin cleavage at Trp4 (steric interference) | **Likely > model prediction** — Wu & Ding (2016, J Pept Sci): Trp-flanked cleavage sites are cut 3–8× slower than Tyr/Phe equivalents | D-Trp Wave 2 plan stands; assay actual stability first — may not need D-modification |

**Recommended action before full MIC panel:**
Run a serum stability screen on all 20 pilot candidates:
- Protocol: 50% pooled human serum, 37°C, time points 0/30/60/120 min, 100 µM peptide
- Quantification: HPLC; include one stable D-peptide as positive stability control
- Cost: ~$200–400 per batch of multiple candidates (not per individual peptide)

This validates the gate assumptions directly and prevents retiring candidates that the model
incorrectly penalises. For SEED-006 and SEED-007 (scores 0.61–0.67), the assay will
determine whether borderline scores translate to the required t½ > 2h.

---

## Troubleshooting

### Too Few Candidates Pass the Gates

If fewer than 10 candidates are nominated from a batch:

1. Check `disagreement` scores — if many candidates cluster near the configured `max_disagreement`
   threshold (0.40 for both phase3.yaml and pipeline.yaml), the two scorers may systematically
   disagree for this peptide series. Consider whether to relax `max_disagreement` in a custom
   config (document the change and the scientific justification).
2. Check `novelty` scores — if the reference set covers your template region well, novelty will
   be low. Consider reducing `min_novelty` for that generation run only.
3. Check `safety` scores — if a hydrophobic template is used, many variants may have low safety.
   Review the safety score components (`scoring/safety.py`) for the specific risk flag.
4. Run `openamp-foundry bench leakage` to confirm candidates are not near-duplicates of each other.

### Synthesis Failure (No Product / Low Purity)

1. Check the presynth QC report for HYDROPHOBIC_RUN or LONG_PEPTIDE flags.
2. Consider pseudoproline (Ψ-Pro) dipeptides for Ser/Thr-containing sequences.
3. Consider microwave-assisted SPPS for sequences with aggregation propensity.
4. For Cys-containing peptides: use Acm protection if disulfide formation is not desired.

### All Candidates Fail Hemolysis

1. Check μH values — a high hydrophobic moment across all candidates suggests the template
   itself is hemolytic.
2. Consider substituting hydrophobic residues (L→A, F→Y) to reduce membrane disruption.
3. Re-score the modified variants through the pipeline before ordering.

---

---

## Negative Result Reporting Protocol

**All results — active and inactive — must be reported.** Selective reporting of only positive
results invalidates the pipeline's active-learning loop and creates publication bias.

### For each inactive candidate

Record the result using the schema at `schemas/lab_result.schema.json` with:

```json
{
  "result_qualitative": "inactive",
  "result_value": 128.0,
  "result_unit": "µg/mL",
  "assay_type": "MIC",
  "notes": "No growth inhibition at 128 µg/mL (top concentration tested). MIC > 128 µg/mL."
}
```

> `result_value` records the **highest concentration tested with no activity** (not `null`).
> This preserves the numerical upper bound, which is required for the active-learning loop.

### What to record for inactive candidates

| Field | Value |
|-------|-------|
| `result_qualitative` | `"inactive"` |
| `result_value` | Highest concentration tested with no activity (e.g. 128.0) |
| `result_unit` | `"µg/mL"` |
| `assay_date` | Date of the assay |
| `positive_control_passed` | Must be `true` — if false, the assay is invalid |
| `notes` | e.g. `"No activity at 128 µg/mL (top concentration). Possible hydrophobic aggregation."` |

### Diagnostic questions for inactive candidates

1. **Is μH > 0.55 and selectivity_proxy < 0.5?** → Likely hemolytic, not inactive
2. **Is synthesis_feasibility < 0.7?** → Possible synthesis failure; request HPLC purity certificate
3. **Is the seed family entirely inactive?** → Scaffold-level failure; report as family-level negative
4. **Did external predictors (CAMPR4, AMPScanner) agree it was AMP?** → Scoring model error; update reference dataset
5. **Was the peptide stored correctly?** → Check freeze-thaw cycles, solubility in MHB

### Archiving

Negative results are archived in `outputs/negative_results/` as individual JSON files named
`<candidate_id>_<assay_date>_negative.json`. The lab_result schema hash links back to the
evidence certificate that nominated the candidate. This creates a full traceability chain
for the eventual publication or open data release.

---

## Confidence Statement

All scores are **heuristic proxies** derived from physicochemical features. They have not been
calibrated against wet-lab activity data for this specific peptide series. The pipeline is a
**nomination tool**, not a predictor of MIC values. Expect a hit rate of 20–40% in initial
screens (consistent with the AMP field literature for computationally nominated candidates).

No antimicrobial activity claim is made until wet-lab confirmation.

---

## References

- CLSI M07-A10: Methods for Dilution Antimicrobial Susceptibility Tests for Bacteria That Grow Aerobically
- Boman HG (2003) Peptide antibiotics and their role in innate immunity. Annu Rev Immunol 13:61–92
- Fjell CD et al. (2011) Designing antimicrobial peptides. Nat Rev Drug Discov 11:37–51
