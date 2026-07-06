# Candidate Evidence Certificate

## Purpose

A candidate evidence certificate is a machine-readable record explaining why a peptide was selected, rejected, or sent for expert review.

It is not proof of biological efficacy.

It proves only that the candidate passed, failed, or was evaluated by a predefined dry-lab process under a specific repository version, configuration, and input set.

## Prime rule

**A certificate must make the candidate easier to reject.**

If the certificate only makes the candidate look impressive, it is incomplete.

A useful certificate exposes evidence, uncertainty, baselines, caveats, and failure modes so a qualified reviewer can decide whether the candidate deserves further attention.

## Claim boundary

A high-scoring certificate may support this claim:

> This candidate is computationally nominated and may be worth expert review under the documented assumptions.

It does not support these claims:

- active;
- safe;
- drug-like;
- clinically useful;
- validated;
- approved;
- therapeutic;
- proven antimicrobial.

See [`PROOF_LADDER.md`](PROOF_LADDER.md) for claim levels.

## Certificate lifecycle

```text
candidate input
  -> validation
  -> feature extraction
  -> scoring
  -> novelty audit
  -> safety-risk flagging
  -> synthesis-risk flagging
  -> baseline comparison
  -> diversity rationale
  -> selection/rejection decision
  -> evidence certificate
  -> human review or archive
```

## Required field groups

A certificate should be organized into field groups.

### 1. Identity

| Field | Meaning |
|---|---|
| `candidate_id` | Stable identifier used across outputs. |
| `sequence` | Exact peptide sequence or safe reference to restricted sequence if release-limited. |
| `sequence_hash` | Hash for reproducibility when full sequence cannot be released. |
| `source` | Generated, imported, seed-derived, control, or external. |
| `panel_id` | Candidate panel or batch identifier. |
| `role_in_panel` | lead, control, baseline, uncertainty_probe, diversity_probe, rejected, etc. |

### 2. Provenance

| Field | Meaning |
|---|---|
| `generated_at` | Timestamp. |
| `pipeline_version` | Package or pipeline version. |
| `repo_commit` | Git commit that produced the certificate. |
| `command` | Command or workflow used. |
| `config_path` | Ranking/scoring config. |
| `config_hash` | Hash of config. |
| `input_path` | Candidate input path or safe reference. |
| `input_hash` | Input hash. |
| `random_seed` | Seed where relevant. |

### 3. Validation

| Field | Meaning |
|---|---|
| `valid_sequence` | Whether sequence passed syntax and alphabet checks. |
| `validation_errors` | Any validation failure. |
| `length` | Sequence length. |
| `canonical_alphabet` | Whether only canonical symbols are present. |
| `duplicate_status` | duplicate, near_duplicate, unique, unknown. |

### 4. Feature evidence

| Field | Meaning |
|---|---|
| `features` | Physicochemical and sequence-derived features. |
| `feature_versions` | Feature extractor versions where available. |
| `feature_warnings` | Feature-level caveats. |

### 5. Scores

| Field | Meaning |
|---|---|
| `scores.activity` | Dry-lab activity-likeness score. |
| `scores.safety` | Safety-risk-adjusted score or safety score. |
| `scores.novelty` | Novelty score against declared references. |
| `scores.synthesis` | Synthesis feasibility score. |
| `scores.ensemble` | Combined score. |
| `scores.disagreement` | Model/scorer disagreement where available. |
| `score_interpretation` | Human-readable interpretation with caveats. |

Scores must not be described as biological proof.

### 6. Baseline comparison

| Field | Meaning |
|---|---|
| `baselines_checked` | Charge, length, hydrophobicity, similarity, random, etc. |
| `baseline_results` | Candidate or panel relation to baselines. |
| `beats_relevant_baselines` | true, false, partial, or unknown. |
| `baseline_caveat` | What simple explanation may still account for selection. |

A candidate selected only because it is highly cationic should say so.

### 7. Novelty audit

| Field | Meaning |
|---|---|
| `references_checked` | Reference sets used. |
| `reference_version` | Version/date/hash of reference set. |
| `nearest_neighbors` | Safe summary of closest known references. |
| `similarity_method` | Alignment or distance method. |
| `novelty_label` | known, close_relative, related_novel, high_confidence_novel, unknown. |
| `novelty_caveat` | Known limitations of reference coverage. |

Novelty is only as strong as the reference set.

### 8. Safety-risk and synthesis-risk evidence

| Field | Meaning |
|---|---|
| `safety_flags` | Predicted hemolysis/cytotoxicity/selectivity concerns. |
| `safety_score_caveat` | Why the safety score may be wrong. |
| `synthesis_flags` | Synthesis or handling difficulty flags at a non-protocol abstraction level. |
| `release_flags` | Whether full sequence or artifact needs release review. |

The certificate must not imply human safety.

### 9. Diversity and selection rationale

| Field | Meaning |
|---|---|
| `cluster_id` | Diversity cluster or scaffold family where available. |
| `structural_class` | Heuristic structural class where available. |
| `selection_reason` | Why the candidate was selected or rejected. |
| `selection_tradeoffs` | Activity vs safety vs novelty vs diversity vs uncertainty. |
| `panel_contribution` | What question this candidate helps the panel ask. |

A batch is an experimental question, not a top-k dump.

### 10. Uncertainty and failure modes

| Field | Meaning |
|---|---|
| `uncertainty` | Overall dry-lab uncertainty if available. |
| `known_failure_modes` | Reasons this candidate may fail. |
| `model_blind_spots` | Known blind spots relevant to this candidate. |
| `unsupported_claims` | Claims the certificate does not support. |

This is the most important section for trust.

### 11. Review and next-step status

| Field | Meaning |
|---|---|
| `recommended_next_steps` | Safe next scientific review steps. |
| `human_review_status` | not_reviewed, needs_review, approved_for_review, rejected, etc. |
| `reviewer_notes` | Human reviewer summary where available. |
| `proof_ladder_level` | Evidence level from [`PROOF_LADDER.md`](PROOF_LADDER.md). |
| `publication_status` | internal, safe_to_publish, restricted, staged, do_not_publish. |

## Minimal certificate example

```json
{
  "candidate_id": "AMPF-000001",
  "sequence_hash": "sha256:...",
  "panel_id": "demo",
  "role_in_panel": "lead",
  "pipeline_version": "0.5.x",
  "repo_commit": "unknown-in-demo",
  "config_hash": "sha256:...",
  "valid_sequence": true,
  "features": {},
  "scores": {
    "activity": 0.0,
    "safety": 0.0,
    "novelty": 0.0,
    "synthesis": 0.0,
    "ensemble": 0.0
  },
  "baselines_checked": ["charge_density", "similarity"],
  "references_checked": ["demo_known_amps"],
  "selection_reason": "Computationally nominated by dry-lab pipeline under demo settings.",
  "known_failure_modes": [
    "Dry-lab score may reflect simple physicochemical similarity rather than true activity.",
    "No wet-lab evidence exists for this candidate."
  ],
  "unsupported_claims": [
    "biological activity",
    "human safety",
    "clinical usefulness"
  ],
  "proof_ladder_level": 4,
  "recommended_next_steps": [
    "Expert review before any experimental decision."
  ]
}
```

## Certificate quality tiers

### Tier 0 — Invalid

Missing identity, provenance, scores, or claim boundary.

### Tier 1 — Basic

Contains identity, sequence or hash, scores, timestamp, pipeline version, and selection reason.

### Tier 2 — Reviewable

Adds novelty audit, safety-risk flags, synthesis-risk flags, failure modes, and proof-ladder level.

### Tier 3 — Baseline-aware

Adds cheap-baseline comparison and explains whether the candidate survives simple explanations.

### Tier 4 — External-review ready

Adds provenance hashes, full panel context, diversity rationale, release status, and human-review fields.

### Tier 5 — Calibration-ready

Links candidate prediction to later structured outcome data without rewriting the original selection rationale.

OpenAMP should aim for Tier 4 before serious external review and Tier 5 after qualified result intake.

## Anti-patterns

### Score dump

A certificate that reports scores but not why they matter.

### Hype certificate

A certificate that makes a candidate look active without assay evidence.

### Missing-baseline certificate

A certificate that does not say whether cheap heuristics explain the selection.

### No-failure-mode certificate

A certificate that lists only reasons to believe.

### Non-reproducible certificate

A certificate without config, commit, input hash, or version.

## Reviewer questions

A reviewer should be able to answer:

1. Why was this candidate selected?
2. Which cheap explanation might account for it?
3. Is it novel or merely similar to known references?
4. What safety risks are predicted?
5. What synthesis or feasibility risks are predicted?
6. What role does it play in the panel?
7. What claim level is justified?
8. What would make this candidate fail review?

If the certificate cannot answer these, improve the certificate.

## Final standard

A candidate evidence certificate should turn an AI-generated candidate into a scientific object that can be inspected, rejected, archived, or cautiously advanced.

It should never turn a dry-lab score into a biological claim.
