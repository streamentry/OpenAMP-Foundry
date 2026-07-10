# Agent Stop-Condition Examples (D6)

This document provides worked examples of when an agent MUST stop and request human review instead of proceeding. See `CLAUDE.md` for the authoritative stop rule.

## Stop rule (from CLAUDE.md)

> Stop and request human review if a change touches safety policy, release policy, candidate release, model release, non-toy data, external-facing artifacts, benchmark thresholds, calibration policy, or public scientific claims.

## Stop-condition taxonomy

| Category | Example trigger | Why it stops |
|---|---|---|
| Safety policy | Lowering the hemolysis rejection threshold | Changes what gets blocked |
| Release policy | Marking a candidate as "cleared for synthesis" | Irreversible wet-lab consequence |
| Benchmark threshold | Changing `PRECISION_AT_K_THRESHOLD` | Changes what counts as a passing model |
| Calibration policy | Auto-approving a recalibration without audit | Corrupts the learning loop |
| Non-toy data | Introducing real sequences into a schema test | Leaks data before human review |
| Public scientific claims | Strengthening the certainty of an evidence certificate | Claim escalation |
| External artifacts | Modifying a released CERT- or RMF- record | Breaks downstream reproducibility |

## Worked examples

### Example 1: Stop on threshold edit

**Scenario:** An agent is implementing a new precision@k benchmark card. While reading the code, it notices the threshold looks too low and edits `PRECISION_AT_K_THRESHOLD = 0.5` to `0.7`.

**Why this stops:** Changing a benchmark threshold changes what passes the benchmark. A model that previously had ranking authority would lose it; one that didn't might gain it. This is not a schema-addition task — it is a governance decision.

**Correct agent behavior:**
```
STOP CONDITION TRIGGERED: Proposed change to PRECISION_AT_K_THRESHOLD.

This threshold controls which models have ranking authority. Changing it
affects all current and future benchmark comparisons and requires human review.

Decision required: Should PRECISION_AT_K_THRESHOLD be changed from 0.5 to 0.7?
Evidence needed: Benchmark results showing current threshold is wrong.

I have NOT made this change. Leaving a decision-log draft in decision_logs/.
```

### Example 2: Stop on proof-ladder upgrade

**Scenario:** An agent is writing a certificate report. It reads the candidate's scores and notices they are very high. It updates `proof_ladder_level` from `dry_lab_candidate` to `computational_validated`.

**Why this stops:** Proof-ladder level upgrades are public scientific claims. Moving a candidate up the ladder implies more evidence than may exist. This is a calibration policy and public claim decision.

**Correct agent behavior:**
```
STOP CONDITION TRIGGERED: Proposed change to proof_ladder_level.

Changing a candidate's proof-ladder level changes what the evidence certificate
claims about the candidate. This requires human review.

I have NOT changed proof_ladder_level. The report uses the existing level.
```

### Example 3: Stop on real data introduction

**Scenario:** An agent is asked to "add more realistic test data." It replaces `TOY-001` with a real sequence from a published AMP database.

**Why this stops:** Non-toy data in tests requires review before appearing in the codebase. Real sequences may have IP, publication, or privacy constraints.

**Correct agent behavior:**
```
STOP CONDITION TRIGGERED: Proposed addition of non-toy candidate data.

The sequence in the suggested test data does not use a TOY-/MOCK-/EXAMPLE- prefix
and appears to be a real AMP sequence. Adding real sequences requires human review.

I have NOT added this sequence. All test data uses TOY- prefix.
```

## How to write a stop-condition decision log

When a stop condition fires, leave a decision log draft:

```markdown
# Decision Log Draft — [brief title]

**Date:** [date]
**Triggered by:** [what action triggered the stop]

## What I found

[Description of the situation]

## What I did NOT change

[Explicit list of changes not made]

## Decision required

[The specific question a human must answer]

## Evidence needed

[What evidence would support a go/no-go decision]
```

File this in `decision_logs/` with a descriptive name. Index it in `decision_logs/INDEX.md`.
