# Artifact Claim Boundaries

## Purpose

Each artifact type produced by the pipeline supports a specific maximum claim level.
This document prevents overclaiming by mapping artifact types to their supported
proof-ladder levels.

## Artifact map

| Artifact | Max claim level | What it supports | What it does NOT support |
|----------|----------------|------------------|-------------------------|
| Candidate certificate | multi_signal_candidate_evidence | Candidate passed dry-lab filters and multi-signature scoring | Biological activity, safety, clinical usefulness |
| Batch report | multi_signal_candidate_evidence | Summary of scored candidates in a batch | Any individual candidate claim |
| Evidence certificate | baseline_triaged to multi_signal_candidate_evidence | Reproducible selection rationale | Biological validation |
| Simulation result | informational only | Experimental proxy output, always informational | Ranking impact unless gate permits |
| Lab result report | initial_qualified_assay_result | Machine-readable assay outcome | Conclusions about efficacy |
| Calibration intake report | informational only | Descriptive join of predictions and outcomes | Recalibration authority |
| Recalibration gate verdict | informational only | Whether recalibration conditions are met | Permission to change weights |
| Benchmark report | leakage_aware_benchmark | Retrospective performance estimate | Real-world generalization |
| Review packet | expert_reviewed_assay_proposal | Candidate evidence for human review | Approval or recommendation |

## Rule

**No artifact may assert a claim higher than its max claim level.**

If an artifact needs to support a higher claim level, it must:
1. Include evidence at that level (e.g., assay results for Level 6)
2. Be reviewed by a qualified human
3. Have its schema updated to reflect the higher level

## Exceptions

The only exception is the final validated discovery claim:
> "An open AI discovery pipeline produced a newly validated antimicrobial peptide family."

This claim requires all 10 conditions from MISSION.md §Headline-grade result and may
only be made after independent wet-lab validation with full evidence trail.
