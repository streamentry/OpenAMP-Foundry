# Assay Pre-Registration — Wave 1

**Status:** PRE-REGISTERED (lock before synthesis order is placed)  
**Pipeline version:** 0.5.x  
**Manifest SHA-256:** see `outputs/phase3_manifest.json`  
**Locked by:** [PI name + date]  
**Document version:** 1.0 (2026-06-28)

---

## Purpose

This document pre-registers the primary assay plan for Wave 1 of the OpenAMP Foundry pilot panel.
Pre-registration means the analysis plan, pass/fail thresholds, and reporting obligations are locked
**before** any wet-lab result is seen. This prevents p-hacking, outcome switching, and selective
non-reporting of negative results.

> **This document must be signed by the PI and filed before synthesis is ordered.**
> Any deviation from this plan must be logged in a deviation record and reported in the methods.

---

## 1. Candidate Set

| Field | Value |
|-------|-------|
| Number of candidates | 20 (pilot panel) |
| Selection algorithm | `pilot-panel` with similarity_threshold=0.75, max_per_seed=4 |
| Selection date | [date of `make pilot` run] |
| Selection locked at manifest | `outputs/phase3_manifest.json` |
| Confident panel (post-external-predictor filter) | TBD after running CAMPR4 / AMPScanner / dbAMP |

---

## 2. Primary Assay — Broth Microdilution MIC

### Protocol

- **Method:** Broth microdilution (EUCAST ISO 20776-1 or CLSI M07)
- **Broth:** Mueller-Hinton Broth II (MHB-II; cation-adjusted for Gram-negative)
- **Volume:** 100 µL per well (96-well plate, flat-bottom)
- **Inoculum:** 5 × 10⁵ CFU/mL (0.5 McFarland ± 10%)
- **Peptide concentration range:** 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128 µg/mL (serial 2-fold)
- **Incubation:** 37 °C, 18–20 h (aerobic, static)
- **Readout:** Optical density at 600 nm (OD600); visual confirmation of turbidity
- **MIC definition:** Lowest concentration with no visible growth (OD600 ≤ 10% of growth control)

### Target Organisms

| Priority | Organism | Strain | Gram | Rationale |
|----------|----------|--------|------|-----------|
| 1 | *Escherichia coli* | ATCC 25922 | Negative | QC reference, EUCAST standard |
| 2 | *Staphylococcus aureus* | ATCC 29213 | Positive | Clinical relevance, MRSA proxy |
| 3 | *Pseudomonas aeruginosa* | ATCC 27853 | Negative | ESKAPE organism, hard target |
| 4 | *Klebsiella pneumoniae* | ATCC 700603 | Negative | Clinical priority, MDR context |

Priority order: if budget-constrained, run organisms 1 and 2 only (minimum viable screen).

### Controls

| Control | Type | Expected result | Action if fails |
|---------|------|-----------------|-----------------|
| Ciprofloxacin 0.004–4 µg/mL vs E. coli ATCC 25922 | Positive | MIC = 0.004–0.016 µg/mL (EUCAST v14 Table 5 QC range) | ABORT assay run; repeat |
| PBS / vehicle only (no peptide) | Negative growth control | Full growth (OD600 > 0.15) | ABORT assay run; repeat |
| Sterility control (broth + peptide, no bacteria) | Sterility | No growth (OD600 ≤ 0.03) | Flag contamination; repeat |

---

## 3. Secondary Assay — Hemolysis (HC50)

### Protocol

- **Cells:** Human red blood cells (hRBCs), freshly drawn (same day) from a consented donor or commercial suspension
- **Buffer:** Phosphate-buffered saline (PBS, pH 7.4)
- **hRBC concentration:** 0.5% v/v
- **Peptide range:** 1, 2, 4, 8, 16, 32, 64, 128, 256, 512 µg/mL
  *(Extended to 512 µg/mL to avoid TI ambiguity at the 32 µg/mL MIC boundary:
  a candidate at MIC=32 µg/mL with HC50>256 would be borderline TI>8, not PASS;
  testing to 512 µg/mL disambiguates whether TI is truly >10.)*
- **Incubation:** 37 °C, 1 h (gentle shaking, 100 rpm)
- **Readout:** Supernatant absorbance at 541 nm after centrifugation (800 × g, 10 min)
- **Controls:**
  - 0.1% Triton X-100 = 100% lysis (positive control)
  - PBS only = 0% lysis (negative control)
- **HC50 definition:** Concentration producing 50% hemolysis (interpolated from sigmoidal fit or linear interpolation)
- **Interpretation rule:** HC50 > 512 µg/mL is reported as "> 512 µg/mL" and counts as PASS for TI ≥ 10 when MIC ≤ 51.2 µg/mL

### Reporting

Report HC50 (µg/mL) for each candidate. If HC50 > 256 µg/mL (top concentration), report as > 256 µg/mL.

---

## 4. Selectivity Index

Compute Therapeutic Index (TI) for each organism:

```
TI = HC50 (µg/mL) / MIC (µg/mL)
```

| TI interpretation | Action |
|-------------------|--------|
| TI > 10 | PASS — proceed to confirmatory assay |
| TI 5–10 | BORDERLINE — note for expert review; may advance if no better candidates |
| TI < 5 | FAIL — exclude from Wave 2 unless exceptional MIC |

---

## 5. Serum Stability Assay (Wave 1 optional, Wave 2 mandatory)

- **Matrix:** 25% human serum in PBS (37 °C)
- **Peptide concentration:** 100 µg/mL
- **Time points:** 0, 0.5, 1, 2, 4 h
- **Readout:** Residual antimicrobial activity by agar dilution or analytical HPLC + MS
- **Pass criterion:** > 50% activity remaining at 2 h

> **Pre-registered decision:** Serum stability is optional in Wave 1 if capacity is limited.
> It becomes mandatory in Wave 2 for any candidate with MIC ≤ 8 µg/mL (tier 1 hits).

---

## 6. Pre-registered Analysis Plan

### Primary Endpoint

**Primary endpoint:** Number of candidates with MIC ≤ 32 µg/mL against *E. coli* ATCC 25922.

**Secondary endpoint:** Number of candidates with MIC ≤ 32 µg/mL AND TI > 10.

### Hit Definition (locked)

A candidate is classified as a **confirmed hit** if:

1. MIC ≤ 32 µg/mL against ≥ 1 target organism (Table in §2), AND
2. TI > 10 (HC50 / MIC > 10), AND
3. Positive control in the same assay plate passed (ciprofloxacin QC range)

A candidate is classified as a **provisional hit** if criterion 1 is met but criterion 2 or 3 could not be assessed (resource constraints). Provisional hits advance to Wave 2 with serum stability and TI gating.

### Statistical Plan

- All assays run in **biological triplicate** (n = 3 independent experiments on separate days)
- Report geometric mean MIC ± SD from triplicates
- Report HC50 with 95% CI (from sigmoidal regression or log-linear interpolation)
- No correction for multiple comparisons for primary endpoint (exploratory screen)
- No data points excluded without documented justification

### Reporting Obligations

- **All results reported**, including:
  - Inactive candidates (MIC > 128 µg/mL)
  - Toxic candidates (TI < 2)
  - Inconclusive results (QC failure with description)
- Negative results archived as `schemas/lab_result.schema.json` entries with `result_qualitative: "inactive"`
- Results shared with pipeline team within 2 weeks of assay completion
- Results NOT selectively shared or suppressed based on outcome

---

## 7. Pre-registered Decision Gates

| Gate | Threshold | Action if passed | Action if failed |
|------|-----------|-----------------|-----------------|
| P1: ≥1 candidate MIC ≤ 32 µg/mL | Hit count ≥ 1 | Proceed to Wave 2 (D-amino variants, MDR strains) | Re-evaluate pipeline; consider new seeds |
| P2: ≥1 candidate TI > 10 + MIC ≤ 32 µg/mL | Hit count ≥ 1 | Proceed to serum stability gating | Return to design; re-weigh selectivity scoring |
| P3: ≥1 candidate all-gates pass (P2 + t½ > 2h + novel scaffold) | Hit count ≥ 1 | Prepare confirmatory external lab replication | Document as negative result; publish pipeline learnings |

---

## 8. Deviations

Any deviation from this protocol must be documented below before assay data is analysed:

| Date | Deviation description | Approved by |
|------|----------------------|-------------|
| — | — | — |

---

## 9. Signatures

| Role | Name | Institution | Signature | Date |
|------|------|-------------|-----------|------|
| Principal Investigator | | | | |
| Peptide Synthesis Approver | | | | |
| Biosafety Officer | | | | |
| Lab Partner Representative | | | | |

---

## 10. Disclaimer

This pre-registration covers a computational nomination pilot. Candidates are short synthetic
peptides derived from natural AMP templates. No claim of clinical efficacy, drug status, or
therapeutic use is made. All wet-lab work must comply with local institutional biosafety
regulations and ethics requirements.
