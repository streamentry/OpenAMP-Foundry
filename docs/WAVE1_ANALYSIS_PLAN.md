# Wave 1 Analysis Plan

**Status:** PRE-REGISTERED — locked before any wet-lab data is seen.  
**Locked at:** 2026-07-06  
**Pipeline version:** 0.5.x  
**Pre-registered by:** OpenAMP agent (pre-registration template)  
**Document version:** 1.0  

No post-hoc changes to this plan are permitted. Any deviation must be
logged in a dated decision log entry (`schemas/decision_log.schema.json`)
and reported alongside results.

---

## 1. Candidate Set

The Wave 1 panel consists of 24 candidates from 15 scaffold families
(see `outputs/wave1_final_panel.csv`). The positive control is
SEED-001_VAR_064 (magainin-1 derivative, expected MIC 4–32 µg/mL).

---

## 2. Primary Analysis

### 2.1 Primary Endpoint

**Number of candidates with MIC ≤ 32 µg/mL against *E. coli* ATCC 25922.**

Reported as: `x / N_candidates` with geometric mean MIC and range.

### 2.2 Primary Success Criterion

The batch is declared a **primary success** if ≥ 3 candidates meet the
primary endpoint.

This threshold is encoded in `configs/wave1_pass_fail.yaml`.

---

## 3. Secondary Analysis

### 3.1 Secondary Endpoint

**Number of candidates with MIC ≤ 32 µg/mL AND therapeutic index (TI) > 10.**

Therapeutic index = HC50 / MIC, where HC50 is the concentration causing
50% hemolysis in human RBC assay.

### 3.2 Secondary Success Criterion

The batch is declared a **secondary success** if ≥ 1 candidate meets
the secondary endpoint.

### 3.3 Hit Definition (locked)

A candidate is a **confirmed hit** if all three conditions hold:

1. MIC ≤ 32 µg/mL against ≥ 1 target organism.
2. TI > 10 (HC50 / MIC > 10).
3. Positive control in the same assay plate passed (expected MIC 4–32).

A candidate is a **provisional hit** if criterion 1 is met but criterion 2
or 3 could not be assessed (resource constraints). Provisional hits advance
to Wave 2 discussion with additional caution.

A candidate is **inactive** if MIC > 32 µg/mL against all tested organisms.

A candidate is **toxic** if TI < 2.

---

## 4. Exploratory Analysis

The following analyses are pre-registered as exploratory. Findings from
these may inform Wave 2 design but will not be used to redefine success
after seeing results.

### 4.1 Per-Family Hit Rate

Stratify results by the 15 scaffold families. Report per-family hit rate
and compare against per-family pipeline scores (ensemble, selectivity,
activity).

### 4.2 Structural Class Analysis

Group candidates by heuristic structural class (cysteine_rich, proline_rich,
short, highly_cationic, moderately_cationic, low_charge). Report whether
any class systematically underperforms or overperforms relative to pipeline
predictions.

### 4.3 Simulation Score Correlation

If `rank --simulation-mode info` was used during candidate selection,
report correlation between simulation scores and observed MIC/TI values.
This is purely informational — simulation scores are not validated for
selection (per SIMULATION_BENCHMARK.md).

### 4.4 Pipeline Calibration

Compare pipeline ensemble, activity, safety, and rich_selectivity scores
against observed outcomes. Compute per-score AUROC and calibration curves
for the 24-candidate set. Note that n=24 is small — treat calibration
findings as qualitative.

---

## 5. Statistical Methods

### 5.1 MIC Reporting

- Report geometric mean MIC from biological triplicates (n = 3 independent
  experiments on separate days).
- Report geometric standard deviation or range.
- No data points excluded without documented justification.

### 5.2 Hemolysis Reporting

- Report HC50 with 95% CI from sigmoidal regression (log[peptide] vs
  % hemolysis, 4-parameter logistic fit).
- Report TI for each candidate.

### 5.3 Multiple Comparisons

No correction for multiple comparisons for the primary and secondary
endpoints (this is an exploratory screen, not a confirmatory trial).

### 5.4 Missing Data

If a candidate cannot be tested (synthesis failure, precipitation,
insufficient quantity), record the reason and exclude from analysis.
Report the exclusion count transparently.

---

## 6. Scenario Handling

### 6.1 All Candidates Inactive

If 0 candidates meet the primary endpoint, publish the negative result.
The batch is still informative for calibration (confirms pipeline false
positive rate). Wave 2 should not proceed without scorer improvement.

### 6.2 All Candidates Toxic

If > 50% of candidates have TI < 2, flag a pipeline safety scorer failure.
Review safety weights and update selection rules. No new candidates should
be synthesized until the safety issue is resolved.

### 6.3 Positive Control Fails

If the positive control MIC falls outside 4–32 µg/mL, the entire assay
batch is invalid. Results may be informative but cannot be used for hit
calling or calibration. Request a repeat assay.

### 6.4 Mixed Results

If some candidates hit and others fail, proceed to exploratory analysis
(§4) to identify what distinguishes hits from failures. Use findings to
inform scorer improvements for Wave 2.

---

## 7. Reporting Obligations

All results will be reported, including:

- Inactive candidates (MIC > 32 µg/mL).
- Toxic candidates (TI < 2).
- Inconclusive results (QC failure with description).
- Synthesis failures (no product / low purity).

Negative results will be archived in `outputs/negative_result_archive.csv`
per the schema in `docs/NEGATIVE_RESULT_ARCHIVE.md`.

---

## 8. Timeline

| Milestone | Expected |
|-----------|----------|
| Data return | Within 2 weeks of assay completion |
| Analysis report | Within 1 week of data return |
| Decision (go/no-go for Wave 2) | Within 1 week of analysis report |

---

## 9. Related Documents

- `configs/wave1_pass_fail.yaml` — Machine-readable pass/fail criteria.
- `scripts/check_wave1_pass_fail.py` — CLI to validate batch results.
- `docs/ASSAY_PREREGISTRATION.md` — Pre-registered assay protocol.
- `docs/LAB_PARTNER_ONBOARDING.md` — Lab partner instructions.
- `schemas/lab_result.schema.json` — Data return schema.
- `schemas/decision_log.schema.json` — Decision log format.
