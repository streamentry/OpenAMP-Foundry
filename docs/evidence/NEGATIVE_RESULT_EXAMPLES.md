# Informative vs Non-Informative Negative Results (F6)

This document provides worked examples contrasting informative and non-informative negative results, to help pipeline users interpret and record negative results correctly.

## The distinction

A negative result is **informative** when it:
- Was produced by a well-calibrated simulation module
- Used an explicit, controlled rejection criterion
- Is traceable to a specific candidate ID and pipeline run
- Has a rejection reason from the controlled vocabulary

A negative result is **non-informative** when it:
- Was produced by a module in a degraded or uncalibrated state
- Used an implicit or ad-hoc criterion ("it looked bad")
- Is missing a candidate ID or pipeline run reference
- Cannot be linked to a specific rejection stage

## Example 1: Informative — hemolysis screen rejection

**NRR- record:**
```json
{
  "nrr_id": "NRR-00147",
  "candidate_id": "TOY-0049",
  "pipeline_run_id": "RUN-2026-0003",
  "simulation_module": "membrane_proxy",
  "rejection_stage": "safety_screen",
  "rejection_reason": "hemolysis_risk",
  "confidence": 0.82,
  "score": 0.87,
  "threshold": 0.70,
  "dry_lab_only": true
}
```

**Why this is informative:**
- `rejection_reason` is from `VALID_REJECTION_REASONS` (hemolysis_risk)
- `confidence` is 0.82 — high enough that calibration can use this signal
- `simulation_module` is named (membrane_proxy) — interpretable if module is well-calibrated
- `score` and `threshold` are explicit — the criterion is reproducible

**How to use it:** This NRR- can enter the FMS- failure mode similarity report to check whether future rejections cluster around this pattern.

## Example 2: Non-informative — module in error state

**Situation:** The membrane_proxy adapter returned an error code (408 timeout) during a run. A score of 0.0 was recorded and the candidate was rejected.

**Why this is NOT informative:**
- The "score" of 0.0 is not a biological prediction — it is a software artifact
- The rejection was due to module unavailability, not candidate quality
- If included in calibration, it would falsely inflate the rejection rate

**Correct handling:**
```json
{
  "nrr_id": "NRR-00148",
  "candidate_id": "TOY-0050",
  "pipeline_run_id": "RUN-2026-0003",
  "simulation_module": "membrane_proxy",
  "rejection_stage": "simulation_error",
  "rejection_reason": "module_error",
  "confidence": 0.0,
  "score": null,
  "threshold": null,
  "is_software_error": true,
  "dry_lab_only": true
}
```

Flag with `is_software_error=True`. This marks the record as non-informative for calibration. The SUC- calibration report for membrane_proxy will record the error-state run.

## Example 3: Informative — dual-use flag rejection

**NRR- record:**
```json
{
  "nrr_id": "NRR-00201",
  "candidate_id": "TOY-0103",
  "pipeline_run_id": "RUN-2026-0005",
  "simulation_module": "safety_classifier",
  "rejection_stage": "dual_use_screen",
  "rejection_reason": "dual_use_concern",
  "confidence": 0.91,
  "score": 0.91,
  "threshold": 0.50,
  "dry_lab_only": true
}
```

**Why this is informative:**
- Dual-use concern is a controlled rejection reason from the safety vocabulary
- Confidence is 0.91 — strong signal
- The stage is `dual_use_screen` — directly interpretable and auditable

**Important:** This record MUST NOT be omitted from negative result archives. Dual-use safety rejections are never discarded — they are especially important for audit trail integrity.

## Example 4: Non-informative — undocumented ad-hoc rejection

**Situation:** A researcher manually looked at the candidate list and removed 12 candidates that "seemed redundant." No rejection stage, reason, or criterion was recorded.

**Why this is NOT informative:**
- No `rejection_reason` — cannot enter controlled vocabulary
- No `score` or `threshold` — criterion is not reproducible
- No `simulation_module` — cannot be attributed to a calibrated assessor
- "Seemed redundant" is an implicit judgment, not a machine-checkable criterion

**Correct alternative:**
Before removing candidates, record a rejection reason using the controlled vocabulary (e.g., `sequence_degeneracy` for redundancy). Run the similarity_neighbor_report to compute explicit novelty scores, then use those scores + a threshold to generate an NRR- for each removed candidate.

## Example 5: Borderline — below-threshold but low-confidence module

**Situation:** A candidate scored 0.72 on ensemble_checker, which has a pass threshold of 0.75. The SUC- report for ensemble_checker shows ECE=0.22 (overconfident, well above OVERCONFIDENCE_THRESHOLD=0.15).

**Assessment:** The rejection reason is valid, but the calibration quality reduces its informational value.

**Correct handling:**
1. Record the NRR- with `rejection_reason=low_selectivity`, `score=0.72`, `threshold=0.75`
2. Add a note: `calibration_note: "module SUC-0047 shows overconfidence (ECE=0.22); confidence estimate may be inflated"`
3. The SUC- record for ensemble_checker should flag this as overconfident
4. Do NOT omit this from the calibration loop — the rejection is still valid; the confidence just needs downweighting

## Summary table

| Example | Informative? | Key distinguishing factor |
|---|---|---|
| 1 — hemolysis rejection | Yes | Explicit criterion, calibrated module |
| 2 — module timeout | No | Software error, not biological prediction |
| 3 — dual-use flag | Yes | Safety screen, must not omit |
| 4 — ad-hoc removal | No | No controlled vocabulary, no score |
| 5 — low-confidence module | Partial | Valid criterion, reduced weight |

## Agent behavior

When processing simulation outputs, an agent MUST:
- Record every rejection as an NRR- with a reason from `VALID_REJECTION_REASONS`
- Set `is_software_error=True` for module error states
- NOT drop borderline-confidence rejections — record them and add a `calibration_note`
- NOT rerun a failing candidate without logging the initial failure
