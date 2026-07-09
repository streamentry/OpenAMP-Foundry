# Negative-Result Informativeness Guide

## Purpose

Not all negative results are equally useful. A negative result that says "failed"
with no context tells future reviewers nothing. A negative result that documents
the specific threshold, the driving features, the assay conditions, and a learning
hypothesis is a calibration asset.

This guide defines what makes a negative-result entry **informative**, gives
concrete examples across all six reason categories, and provides a quick-reference
checklist for human and agent contributors.

## The Seven Dimensions of Informativeness

| # | Dimension | What it measures | Why it matters |
|---|-----------|---|---|
| 1 | **Identity** | Is the candidate uniquely identified (candidate_id, sequence)? | Without identity, the entry cannot be linked to pipeline outputs or other batches. |
| 2 | **Context** | Are pipeline_version, source_batch, and date recorded? | Without context, you cannot know which rules or scores were in effect. |
| 3 | **Specificity** | Does reason_detail include concrete values, thresholds, or driving features? | Vague reasons cannot be acted on. Specific reasons enable threshold analysis. |
| 4 | **Actionability** | Does the entry enable a specific action or learning (tighten a gate, flag a scorer weakness, redesign a candidate class)? | Entries that only record failure without analysis cannot improve the pipeline. |
| 5 | **Verifiability** | Are scores and/or assay results included so the claim could be reproduced or checked? | Unverifiable entries cannot be distinguished from errors. |
| 6 | **Structured metadata** | Are category-appropriate conditional fields populated (assay_type/result/unit for lab entries, superseded_by for corrections)? | Structured fields enable machine analysis across entries. |
| 7 | **Interpretation** | Do reviewer_notes include analysis, caveats, or learning hypotheses? | Interpretation turns a data point into actionable knowledge. |

### Classification

| Class | Score range | Meaning |
|-------|-----------|---------|
| **INFORMATIVE** | 6.0–7.0 | Full documentation with analysis. Calibration asset. |
| **NEUTRAL** | 3.5–5.5 | Basic information present but lacks analysis or specificity. |
| **NON_INFORMATIVE** | 0.0–3.0 | Missing critical fields. Cannot be used for learning. |

---

## Examples by Category

### 1. Pre-selection reject

#### Non-informative

```
entry_id: 101
candidate_id: WAVE0.5-101
sequence: ACDEFGHIKLMNPQRSTVWY
reason_category: pre_selection_reject
reason_detail: "Failed safety check."
pipeline_version: v0.5.76
source_batch: wave0.5
date: 2026-07-09
```

Why it is non-informative: The reason_detail says nothing about which safety
check failed, what the threshold was, what score the candidate received, or
whether this was a systematic or candidate-specific issue. No reviewer_notes.

#### Informative

```
entry_id: 201
candidate_id: WAVE0.5-201
sequence: KKKKLLLLKKKKLLLLKKKK
reason_category: pre_selection_reject
reason_detail: "Safety score 0.31 below minimum threshold 0.50. Driving factor: high hemolysis proxy (0.89) from elevated hydrophobicity (GRAVY=1.2). Candidate is a designed amphipathic helix with alternating K/L pattern typical of membrane-active peptides."
pipeline_version: v0.5.76
source_batch: wave0.5
date: 2026-07-09
score_activity: 0.82
score_safety: 0.31
score_novelty: 0.91
score_ensemble: 0.68
reviewer_notes: "Rejected at Gate W0.5-3. High GRAVY is structural — the alternating K/L pattern is the intended mechanism, not an assay risk artifact. Consider whether the safety gate should distinguish between designed membrane activity and non-specific toxicity via a two-tier flag."
```

Why it is informative: Documents the specific threshold (0.50), the driving
feature (GRAVY=1.2 with hemolysis proxy 0.89), all relevant scores, and
captures a hypothesis about whether the rule needs adjustment. The
reviewer_notes provide context that a future reviewer or recalibration
engine can use.

---

### 2. Pipeline reject (after scoring)

#### Non-informative

```
entry_id: 102
candidate_id: PHASE3-042
sequence: AAAAAAKKKKKKAAAAAA
reason_category: pipeline_reject
reason_detail: "Low ensemble score."
pipeline_version: v0.5.76
source_batch: phase3
date: 2026-07-09
```

Why it is non-informative: "Low" compared to what? No threshold, no scores,
no indication of which ensemble components drove the low result.

#### Informative

```
entry_id: 202
candidate_id: PHASE3-142
sequence: GGGGKKKKGGGGKKKKGG
reason_category: pipeline_reject
reason_detail: "Ensemble score 0.42 below synthesis gate threshold 0.65. Activity score 0.38 (activity scorer penalised low hydrophobicity GRAVY=-0.8). Safety score 0.91 acceptable. Dominant failure mode: activity scorer assumes amphipathic helicity, but sequence is glycine-rich with no helical propensity."
pipeline_version: v0.5.76
source_batch: phase3
date: 2026-07-09
score_activity: 0.38
score_safety: 0.91
score_novelty: 0.72
score_ensemble: 0.42
reviewer_notes: "This sequence class (glycine-rich, low hydrophobicity) is systematically undervalued by the activity scorer. Similar sequences in other phase3 batches show the same pattern. Recommend evaluating whether the activity scorer needs a non-helical fallback or whether glycine-rich candidates should be flagged for alternative scoring."
```

Why it is informative: Every score is documented, the specific threshold is
given, the failure mode is analysed (activity scorer assumptions vs actual
sequence properties), and the reviewer identifies a systematic issue that
warrants pipeline improvement.

---

### 3. Diversity reject

#### Non-informative

```
entry_id: 103
candidate_id: SEED-015_VAR_009
sequence: KLLKLLLKLLLKLLK
reason_category: diversity_reject
reason_detail: "Too similar to existing candidate."
pipeline_version: v0.5.76
source_batch: wave0.5b
date: 2026-07-09
```

Why it is non-informative: No similarity metric, no reference candidate,
no threshold — impossible to know whether the diversity filter is working
as intended or over-rejecting.

#### Informative

```
entry_id: 203
candidate_id: SEED-015_VAR_009
sequence: KLLKLLLKLLLKLLK
reason_category: diversity_reject
reason_detail: "Edit-distance similarity 0.88 to SEED-015_VAR_005 (KLLKLLLKLLLKLL) exceeds diversity gate threshold 0.70. The single K→L substitution at position 7 does not provide sufficient sequence diversity for a separate panel slot. Both share the same scaffold (SEED-015, alternating K/L helix)."
pipeline_version: v0.5.76
source_batch: wave0.5b
date: 2026-07-09
score_activity: 0.81
score_safety: 0.67
score_novelty: 0.55
score_ensemble: 0.68
reviewer_notes: "Correct rejection. The candidate is a point mutant of an already-represented scaffold. If we want more SEED-015 diversity, we should design variants with non-conservative substitutions at multiple positions, not single-residue changes."
```

Why it is informative: Specifies the metric (edit-distance), the threshold
(0.70), the reference candidate, what the actual difference is, and includes
a design recommendation.

---

### 4. Reviewer reject

#### Non-informative

```
entry_id: 104
candidate_id: SEED-008_VAR_003
sequence: WFWFRWRWFWFRWR
reason_category: reviewer_reject
reason_detail: "Rejected by expert reviewer."
pipeline_version: v0.5.76
source_batch: wave1
date: 2026-07-09
```

Why it is non-informative: No reviewer identity, no rationale, no reference
to the review criteria that were violated.

#### Informative

```
entry_id: 204
candidate_id: SEED-008_VAR_003
sequence: WFWFRWRWFWFRWR
reason_category: reviewer_reject
reason_detail: "Rejected by Dr. A. Reviewer (Institution) on 2026-07-08. Safety concern: 8 Trp residues (Trp fraction 0.57) create dual-use concern per DUAL_USE_REVIEW_GUIDE v1.2 section 4.3. Reviewer notes the candidate has high membrane-permeation potential that could enable non-therapeutic applications."
pipeline_version: v0.5.76
source_batch: wave1
date: 2026-07-09
score_activity: 0.79
score_safety: 0.44
score_novelty: 0.88
score_ensemble: 0.70
reviewer_notes: "Dual-use concern is valid. The candidate's Trp-rich pattern enables membrane translocation — a feature that is desirable for antimicrobial activity but also confers cell-penetrating capability. This candidate was correctly flagged for expert review per DUAL_USE_REVIEW_POLICY. The rejection should stand unless new evidence demonstrates selective antimicrobial mechanism without mammalian cell penetration."
```

Why it is informative: Names the reviewer (institutional accountability),
cites the specific policy violated (DUAL_USE_REVIEW_GUIDE v1.2 §4.3),
documents the structural feature causing the concern, and the reviewer_notes
explain why this rejection is important and what would be needed to overturn it.

---

### 5. Lab inactive

#### Non-informative

```
entry_id: 105
candidate_id: WAVE0.5-105
sequence: RRRRIIIIRRRRIIII
reason_category: lab_inactive
reason_detail: "Not active."
pipeline_version: v0.5.76
source_batch: wave0.5
date: 2026-07-09
assay_type: MIC
```

Why it is non-informative: "Not active" — at what concentration? Against
which strain? Was the positive control working? Was the assay valid? No
assay_result or assay_unit. No reviewer_notes.

#### Informative

```
entry_id: 205
candidate_id: WAVE0.5-205
sequence: RRIRIIRRIRIIRRI
reason_category: lab_inactive
reason_detail: "MIC > 128 ug/mL against E. coli ATCC 25922, S. aureus ATCC 29213, and P. aeruginosa ATCC 27853. No detectable activity up to 256 ug/mL in any of 3 biological replicates. Positive control (polymyxin B) showed expected MIC 1-2 ug/mL against E. coli, confirming assay validity."
pipeline_version: v0.5.76
source_batch: wave0.5
date: 2026-07-09
assay_type: MIC
assay_result: ">128"
assay_unit: ug/mL
score_activity: 0.78
score_safety: 0.85
score_novelty: 0.62
score_ensemble: 0.75
reviewer_notes: "Activity score 0.78 was a false positive. Sequence is net-charge +7 with moderate amphipathicity — the activity scorer likely overvalued the charge component. This candidate class (Arg-Ile alternating pattern with no hydrophobic core) appears to be a recurring false-positive motif. Consider tracking this pattern for activity-scorer recalibration."
```

Why it is informative: Reports multi-strain testing with 3 biological
replicates, confirms assay validity (positive control data), documents the
exact concentration range tested, and identifies a recurring false-positive
pattern for pipeline improvement.

---

### 6. Lab toxic

#### Non-informative

```
entry_id: 106
candidate_id: WAVE0.5-106
sequence: LLLLKKKKLLLLKKKK
reason_category: lab_toxic
reason_detail: "Toxic in hemolysis assay."
pipeline_version: v0.5.76
source_batch: wave0.5
date: 2026-07-09
assay_type: hemolysis_RBC
```

Why it is non-informative: "Toxic" — at what concentration? What was the
HC50? How many replicates? Was the negative control valid? Without assay
result and unit, the entry is a judgement call with no supporting data.

#### Informative

```
entry_id: 206
candidate_id: WAVE0.5-206
sequence: LKKLLKKLLKKLKKL
reason_category: lab_toxic
reason_detail: "100% hemolysis at 50 uM (human RBC, pooled donors). HC50 = 6.2 uM. Dose-response curve shows steep transition between 2.5 uM (12% hemolysis) and 10 uM (78% hemolysis). Assay positive control (0.1% Triton X-100) showed 100% hemolysis. Negative control (PBS) showed 0.8% hemolysis. 3 technical replicates per concentration."
pipeline_version: v0.5.76
source_batch: wave0.5
date: 2026-07-09
assay_type: hemolysis_RBC
assay_result: "100"
assay_unit: "%"
score_activity: 0.76
score_safety: 0.54
score_novelty: 0.91
score_ensemble: 0.74
reviewer_notes: "Computational safety score 0.54 was below the 0.50 threshold but only marginally. The steep dose-response (2.5 uM → 10 uM transition) suggests a cooperative membrane-disruption mechanism typical of amphipathic helices. Current safety scorer does not model dose-response steepness. Consider adding a cooperativity penalty for candidates with steep hemolysis transitions."
```

Why it is informative: Full dose-response data, HC50 value, control validity,
replicate count, and a specific improvement recommendation (cooperativity
penalty based on dose-response steepness).

---

### 7. Synthesis failure

#### Non-informative

```
entry_id: 107
candidate_id: WAVE0.5-107
sequence: CCCCGGGGCCCCGGGG
reason_category: synthesis_failure
reason_detail: "Could not synthesize."
pipeline_version: v0.5.76
source_batch: wave0.5
date: 2026-07-09
```

Why it is non-informative: "Could not synthesize" is vague. Was it a purity
issue? A yield issue? An aggregation problem? Without details, the same
failure will recur if the candidate is reordered from a different vendor.

#### Informative

```
entry_id: 207
candidate_id: WAVE0.5-207
sequence: CCCCCCCCCKKKKKKK
reason_category: synthesis_failure
reason_detail: "Synthesis failed at purification stage. Crude purity 24% by HPLC (target > 80%). Major byproducts: des-Cys truncations at positions 3 and 7 (confirmed by MS). The poly-Cys N-terminal region causes aggregation during Fmoc deprotection. Two vendor attempts (vendor A and vendor B) both failed with similar impurity profiles. Synthesis difficulty score was 0.31 (below 0.50 feasibility threshold)."
pipeline_version: v0.5.76
source_batch: wave0.5
date: 2026-07-09
score_activity: 0.84
score_safety: 0.72
score_novelty: 0.67
score_ensemble: 0.74
reviewer_notes: "The synthesis score correctly predicted failure (0.31). The poly-Cys motif is known to cause aggregation during SPPS. Future designs should avoid >3 consecutive Cys residues. If this scaffold is needed, consider using pseudoproline or other difficult-sequence chemistries — but this would increase cost significantly."
```

Why it is informative: Documents the specific failure mode (poly-Cys
aggregation), provides quantitative data (24% purity, 2 vendor attempts),
confirms the pipeline's synthesis score was accurate, and gives a design
rule to prevent recurrence.

---

## Before / After Pairs

### Before (non-informative)

```
entry_id: 301
reason_detail: "Failed safety check."
```

### After (informative)

```
entry_id: 301
candidate_id: BATCH-X-042
sequence: KKKLKKKLKKKLKKK
reason_category: pre_selection_reject
reason_detail: "Safety score 0.28 below threshold 0.50. Hemolysis proxy 0.92 from charge density +6.2 (net charge +8, length 14). All 4 high-charge candidates in batch BATCH-X show similar safety scores — batch-level pattern."
pipeline_version: v0.5.76
source_batch: BATCH-X
date: 2026-07-09
score_activity: 0.85
score_safety: 0.28
score_ensemble: 0.59
reviewer_notes: "Batch-level pattern: all high-charge candidates failing safety. This is expected for short, highly cationic sequences. No individual candidate anomaly. Track whether this batch's failure rate is within expected distribution for high-charge designs."
```

### Before (non-informative)

```
entry_id: 302
assay_result: ">64"
assay_unit: ug/mL
reason_detail: "MIC too high."
```

### After (informative)

```
entry_id: 302
candidate_id: BATCH-Y-015
sequence: RLLRLLRLLRLLRLL
reason_category: lab_inactive
reason_detail: "MIC > 64 ug/mL against E. coli ATCC 25922. Tested up to 128 ug/mL. No zone of inhibition in disk diffusion at 50 ug/disk. Positive control (gentamicin) MIC = 1 ug/mL. Negative control (DMSO 1%) showed no inhibition. n=3 biological replicates."
pipeline_version: v0.5.76
source_batch: BATCH-Y
date: 2026-07-09
assay_type: MIC
assay_result: ">64"
assay_unit: ug/mL
score_activity: 0.71
score_safety: 0.88
score_ensemble: 0.69
reviewer_notes: "Borderline activity score (0.71) with no actual activity. The candidate is a low-charge (+3), moderate-GRAVY design — the activity score may have been inflated by moderate hydrophobicity rather than genuine antimicrobial features. This is consistent with the known weakness of the activity scorer on non-cationic candidates."
```

---

## Quick-Reference Checklist

Use this checklist when writing or reviewing a negative-result entry. Each
"yes" earns 1 point toward the informativeness score.

### Identity (1 point)
- [ ] candidate_id is non-empty and specific
- [ ] sequence is a valid amino-acid string

### Context (1 point)
- [ ] pipeline_version is recorded
- [ ] source_batch is recorded
- [ ] date is in ISO 8601 format

### Specificity (1 point)
- [ ] reason_detail includes a specific numeric threshold or value
- [ ] reason_detail identifies the driving feature or failure mode

### Actionability (1 point)
- [ ] The entry enables a specific action (tighten gate, fix scorer, redesign class)
- [ ] Multiple similar entries would reveal a systematic issue

### Verifiability (1 point)
- [ ] Scores are present (score_activity, score_safety, etc., where applicable)
- [ ] Assay results include numeric values and units (where applicable)

### Structured metadata (1 point)
- [ ] Category-appropriate conditional fields are populated
- [ ] superseded_by is set if this entry corrects a prior entry

### Interpretation (1 point)
- [ ] reviewer_notes contain analysis beyond restating the reason_detail
- [ ] reviewer_notes identify a learning hypothesis or pipeline improvement

## Scoring

Count ✓ marks: ____ / 14 possible half-points → ____ / 7 total points

| Score | Classification |
|-------|---------------|
| 6.0–7.0 | **INFORMATIVE** — calibration asset |
| 3.5–5.5 | **NEUTRAL** — basic data present, analysis missing |
| 0.0–3.0 | **NON_INFORMATIVE** — cannot support learning |

## Limitations

- Informativeness scoring is heuristic. A score of 7.0 does not guarantee
  that the entry is scientifically correct — only that it is well-documented.
- A non-informative entry may contain genuinely important negative data that
  the submitter simply did not document well. Missing structure does not mean
  missing signal.
- The framework assumes the entry is intended for machine analysis and
  human review. Some entries may be intentionally sparse (e.g., privacy-
  constrained dual-use rejections); those should be flagged as such rather
  than classified as non-informative.
- Informativeness is not a review of scientific validity. An informative
  entry about an incorrect conclusion is still well-documented — and more
  useful than a non-informative entry about a correct one.
