# Negative Result Archive

## Purpose

This document is the public archive of failed candidates, rejected sequences, and
negative experimental outcomes from the OpenAMP Foundry pipeline. It exists because:

1. **Publishing failures prevents duplicated effort** — another group seeing "we tested
   40 candidates and found 0 hits" saves them from testing the same candidates.
2. **Negative data calibrates the pipeline** — the recalibration engine needs
   confirmed negatives to compute AUROC, precision, and calibration deltas.
3. **Honesty requires it** — AGENTS.md rule 3 says "A clean failure is more valuable
   than a fake success."

## Scope

This archive covers:

- **Pre-selection rejects**: candidates eliminated by safety, novelty, or synthesis
  gates before ever reaching a lab. These are still informative: they show where
  the pipeline's own rules blocked candidates.
- **Selected-but-untested**: candidates that passed all gates but were never
  synthesized or assayed (e.g., deprioritised by budget or scope changes).
- **Lab-tested inactives**: candidates that went through assay and were confirmed
  inactive (MIC > cutoff, no observable antimicrobial activity).
- **Lab-tested toxic**: candidates that passed computational safety gates but
  showed hemolysis or cytotoxicity in assay.
- **Control failures**: assay batches where positive or negative controls failed,
  invalidating the batch. The batch results are archived but flagged as invalid.

## Format

Each entry follows the same JSON-ish structure and is stored as a row in the
archive CSV at `outputs/negative_result_archive.csv`. The CSV is append-only:
entries are never deleted, only corrected with a `superseded_by` field.

### Entry Schema

```text
Field               | Required | Description
--------------------|----------|-----------------------------------------------
entry_id            | Yes      | Monotonic integer (auto-increment)
date                | Yes      | ISO 8601 date of entry
candidate_id        | Yes      | Pipeline candidate identifier
sequence            | Yes      | Amino-acid sequence
reason_category     | Yes      | One of: `pre_selection_reject`, `selected_untested`,
                    |          | `lab_inactive`, `lab_toxic`, `control_failure`,
                    |          | `synthesis_failure`
reason_detail       | Yes      | Human-readable explanation
pipeline_version    | Yes      | Pipeline version at time of rejection/assay
source_batch        | Yes      | Batch name (e.g., "wave0.5", "phase3", "wave1")
assay_type          | Conditional| Assay type if lab-tested (e.g., MIC, hemolysis_RBC)
assay_result        | Conditional| Quantitative result if applicable
assay_unit          | Conditional| Unit (e.g., ug/mL, % hemolysis)
score_activity      | No       | Pipeline activity score at selection time
score_safety        | No       | Pipeline safety score at selection time
score_novelty       | No       | Pipeline novelty score at selection time
score_ensemble      | No       | Pipeline ensemble score at selection time
recalibration_used  | No       | Whether recalibration had occurred before this batch
superseded_by       | No       | entry_id of a correction if this entry was updated
reviewer_notes      | No       | Free-text notes from human review
```

### Example Entries

```csv
entry_id,date,candidate_id,sequence,reason_category,reason_detail,pipeline_version,source_batch,assay_type,assay_result,assay_unit,score_activity,score_safety,score_novelty,score_ensemble,recalibration_used,superseded_by,reviewer_notes
1,2026-08-01,WAVE0.5-001,ACDEFGHIKLMNPQRSTVWY,pre_selection_reject,"Net charge +9 exceeds safety gate max_charge=+8",v0.5.49,wave0.5,,,,,0.85,0.12,0.92,0.63,no,,"Rejected by Gate W0.5-3 (safety)"
2,2026-08-15,WAVE0.5-012,ACDEFGHIKLMNPQRSTVWY,lab_inactive,"MIC > 64 ug/mL against E. coli (ATCC 25922)",v0.5.49,wave0.5,MIC,128,ug/mL,0.82,0.79,0.88,0.83,no,,"Tested as part of Wave 0.5 batch 1"
3,2026-09-01,WAVE0.5-008,ACDEFGHIKLMNPQRSTVWY,lab_toxic,"100% hemolysis at 50 uM (RBC assay)",v0.5.49,wave0.5,hemolysis_RBC,100,%,0.76,0.54,0.91,0.74,no,,"Computational safety score 0.54 was below threshold but not low enough — consider tightening safety gate"
```

## Procedures

### When to add an entry

1. **Pre-selection reject**: automatically recorded by `filter_wave*` scripts.
   The script appends a row to the archive CSV with `reason_category=pre_selection_reject`.
2. **Selected but untested**: when a candidate is removed from an assay queue
   (e.g., budget cut, expired synthesis quote), a human adds the entry.
3. **Lab result received**: when `calibration-intake` processes a lab result with
   MIC > cutoff or hemolysis > threshold, it appends a row automatically.
   A human may add additional `reviewer_notes`.
4. **Control failure**: recorded automatically when the gate detects a failed
   control. The entry links to the full batch by `source_batch`.

### What not to include

- **No full sequences of dangerous or dual-use candidates** unless the safety
  review explicitly approves publication. Truncated identifiers may be used.
- **No personally identifiable information** about lab personnel.
- **No proprietary assay protocols** from CRO partners without their consent.

## Automation

The archive CSV lives at `outputs/negative_result_archive.csv` and is:

- **Read by**: `calibration-intake` (joins against known negatives for cohort metrics),
  recalibration gate (checks for recent negative-lab-history patterns).
- **Written by**: `filter_wave*` scripts (auto-append pre-selection rejects),
  `calibration-intake` (auto-append lab-tested inactives/toxic),
  human operators (manual entries via form or YAML-to-CSV conversion).
- **Validated by**: `scripts/validate_negative_archive.py` (if it exists) —
  checks schema conformance, missing required fields, valid reason_category values.

## Informative vs Non-informative Examples

### Non-informative

```
entry_id: 42
reason_detail: "Failed safety check."
```
Why it's non-informative: No threshold given, no score context, no way to learn from this. Was the safety gate too strict? Too lenient?

### Informative

```
entry_id: 43
candidate_id: WAVE0.5-015
sequence: ACDEFGHIKLMNPQRSTVWY
reason_category: pre_selection_reject
reason_detail: "Safety score 0.31 below minimum threshold 0.50. Driving factor: high hemolysis proxy (0.89) from elevated hydrophobicity (GRAVY=1.2)."
pipeline_version: v0.5.49
score_activity: 0.82
score_safety: 0.31
reviewer_notes: "Rejected at Gate W0.5-3. High GRAVY is structural — candidate is a membrane-interacting peptide — but current policy does not distinguish between assay risk and real toxicity. Consider whether GRAVY threshold should use a two-tier flag approach."
```
Why it's informative: Documents the specific threshold, the driving feature, and captures a hypothesis about whether the rule needs adjustment.

### Informative (lab-tested)

```
entry_id: 44
candidate_id: WAVE0.5-020
reason_category: lab_inactive
reason_detail: "MIC > 128 ug/mL against E. coli ATCC 25922, S. aureus ATCC 29213, and P. aeruginosa ATCC 27853. No activity detected up to 256 ug/mL in any strain."
assay_type: MIC
assay_result: ">128"
assay_unit: ug/mL
score_activity: 0.78
score_safety: 0.85
reviewer_notes: "Activity score 0.78 was a false positive. Candidate is net-charge +8 with moderate GRAVY — activity score may have been charge-dominated. This failure supports tightening charge-bias detection in the activity scorer."
```
Why it's informative: Reports multi-strain testing, captures the specific failure mode, and documents a learning hypothesis that could improve the pipeline.

## Limitations

- This archive is only as complete as the entries added. Gaps mean the pipeline
  has not been tested against those failure modes.
- Pre-selection rejects reflect pipeline rules that may have changed since the
  rejection. The `pipeline_version` field captures which rules were active.
- Lab-tested inactives are not proof of universal inactivity — only inactivity
  against the specific strains and conditions tested.
- The archive may contain duplicate sequences across different batches. This is
  intentional: the same sequence may fail for different reasons in different
  contexts.
