# Disconfirming Test Record (DTR-)

## Purpose

`DTR-` records one explicit attempt to prove a computational claim wrong. It
turns the pre-PR disconfirming pass in `CLAUDE.md` into an inspectable artifact
that can be reviewed alongside a benchmark, evidence certificate, or handoff
packet.

This is a dry-lab record. It documents challenge evidence; it does not create
biological evidence or authorize candidate release.

## Current status

- **Artifact:** `DTR-` disconfirming test record.
- **Implementation:** `src/openamp_foundry/evidence/disconfirming_test_record.py`.
- **Aggregate gate:** `ACDG-` aggregates DTR- records for one pipeline version
  and blocks a verified verdict while claim-affecting follow-up remains
  unresolved.
- **CLI:** `openamp-foundry phase-ac-disconfirming-gate-check --entry-json ...`
  returns JSON or text and exits nonzero for partial or not-established
  verdicts. `make phase-ac-disconfirming-gate-check` runs a safe toy example.
- **Stability:** Experimental. The record and aggregate are internal review
  controls, not release gates or biological validation.
- **Safe boundary:** `dry_lab_only` is always `True`.

The record can show that a claim survived one stated challenge. It cannot show
that the claim is biologically valid, that all relevant challenges were run, or
that a candidate is ready for synthesis or testing.

## Required fields

| Field | Meaning |
|---|---|
| `dtr_id` | Unique identifier with the `DTR-` prefix. |
| `pipeline_version` | Version or commit context for the claim under test. |
| `claim_tested` | The precise claim being challenged, limited to 400 characters. |
| `test_type` | One of the controlled challenge categories below. |
| `test_description` | What was run and what comparison or failure mode it targeted. |
| `test_outcome` | `not_refuted`, `refuted`, `inconclusive`, or `skipped`. |
| `evidence_summary` | Short, reviewable summary of the observed result. |
| `limitations` | At least one limitation or remaining uncertainty. |
| `created_at` | Creation timestamp or date. |

`required_action` and `is_claim_affected` are derived from `test_outcome`; do
not hand-edit them. A `refuted` result sets `is_claim_affected=True` and
requires `downgrade_claim`. An `inconclusive` result requires `investigate`.
`not_refuted` and `skipped` do not by themselves justify a stronger claim.

## Controlled challenge categories

| `test_type` | Cheapest question it asks |
|---|---|
| `cheapest_explanation_check` | Could a simple heuristic explain the result? |
| `leakage_check` | Could contamination or near-duplicate leakage explain it? |
| `scope_creep_check` | Did the change exceed the named task or claim scope? |
| `hidden_certainty_check` | Did wording or caveats become stronger than the evidence? |
| `uninformative_uncertainty_check` | Is uncertainty effectively constant across sensible and absurd inputs? |
| `charge_matched_enemy_check` | Does a charge-matched baseline remove the apparent improvement? |
| `train_test_split_check` | Does the result survive a defensible split? |

## Review workflow

1. State the claim before looking at the challenge result.
2. Choose the cheapest plausible challenge that could change the claim.
3. Record the command, comparison, or inspection in `test_description` and
   summarize the evidence without hiding negative results.
4. Record at least one limitation, even when the result is `not_refuted`.
5. Treat `refuted` as a claim-downgrade trigger and `inconclusive` as an
   investigation trigger.
6. Keep the record attached to the relevant review artifact. A DTR- record is
   evidence about the challenge, not a substitute for benchmark, safety,
   novelty, reproducibility, or human-review evidence.
7. Aggregate the records with the Phase AC CLI before treating the disconfirming
   pass as complete. A zero-record, partial, or unresolved aggregate must stay
   visible to reviewers through its nonzero exit status.

## Example shape

```python
from openamp_foundry.evidence.disconfirming_test_record import (
    build_disconfirming_test_record,
)

record = build_disconfirming_test_record(
    dtr_id="DTR-001",
    pipeline_version="edb432d",
    claim_tested="The selection signal is not explained by charge alone.",
    test_type="charge_matched_enemy_check",
    test_description="Compared the pipeline score with a charge-matched baseline on the same split.",
    test_outcome="inconclusive",
    evidence_summary="The matched comparison was underpowered for a decisive conclusion.",
    limitations=["No wet-lab outcome is represented."],
    created_at="2026-07-14",
)
```

The example is a schema-shape example only. It is not a benchmark result and
does not support a biological or ranking claim.

## Limitations and non-claims

- A record is only as useful as the challenge definition and evidence summary.
- `not_refuted` means this recorded test did not refute the claim; it does not
  establish the claim.
- `skipped` preserves the missing check but provides no positive evidence.
- The aggregate gate does not define which challenges are sufficient for every
  claim; it only checks the records supplied for one pipeline version and their
  explicit follow-up state.
- No DTR- record changes ranking authority, release status, safety status, or
  proof-ladder level.

Related: [`PROOF_LADDER.md`](PROOF_LADDER.md),
[`BENCHMARK_GOVERNANCE.md`](BENCHMARK_GOVERNANCE.md),
[`CLAIM_REVIEW_CHECKLIST.md`](CLAIM_REVIEW_CHECKLIST.md), and
[`../engineering/SCHEMA_REGISTRY.md`](../engineering/SCHEMA_REGISTRY.md).
