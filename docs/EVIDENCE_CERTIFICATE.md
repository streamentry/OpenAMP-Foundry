# Candidate Evidence Certificate

A candidate evidence certificate is a machine-readable record explaining why a peptide was selected.

It is not proof of biological efficacy.

It proves only that the candidate passed a predefined dry-lab selection process.

## Required fields

| Field | Meaning |
|---|---|
| `candidate_id` | Stable ID |
| `sequence` | Exact peptide sequence |
| `features` | Physicochemical features |
| `scores` | Activity, safety, novelty, synthesis, ensemble |
| `references_checked` | Reference sets used for novelty checks |
| `selection_reason` | Why this candidate was selected |
| `known_failure_modes` | Reasons this candidate may fail |
| `recommended_next_steps` | Safe next scientific review steps |
| `generated_at` | Timestamp |
| `pipeline_version` | Version of the pipeline |
| `config_hash` | Hash of ranking configuration |

## Interpretation

A high-scoring candidate means:

> Worth expert review and possible assay consideration.

It does not mean:

> Active, safe, drug-like, clinically useful, or approved.
