# Publication and Public Claims Policy

## Purpose

This policy defines how OpenAMP Foundry should communicate results in README text, releases, papers, posters, abstracts, talks, blog posts, social media, funder updates, and partner-facing material.

Public communication is part of the scientific system.

A careless claim can damage trust even when the code is safe.

## Prime rule

**Publish the evidence level, not the excitement level.**

## Scope

This policy applies to:

- public release notes;
- README and website text;
- candidate summaries;
- benchmark reports;
- external review packets;
- scientific manuscripts;
- posters and talks;
- grant or funder updates;
- press language;
- agent-generated summaries.

## Required before public scientific claims

Before public claims, complete:

1. Proof-ladder mapping.
2. Claim review checklist.
3. Safety review if sensitive artifacts are involved.
4. Benchmark source-of-truth check.
5. Release-status check.
6. Negative-result and limitation review.
7. Decision record for major claim upgrades.

Use:

- [`PROOF_LADDER.md`](PROOF_LADDER.md)
- [`CLAIM_REVIEW_CHECKLIST.md`](CLAIM_REVIEW_CHECKLIST.md)
- [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md)
- [`SAFETY.md`](../SAFETY.md)

## Allowed dry-lab language

Allowed for computational-only outputs:

- computationally nominated candidate;
- dry-lab candidate;
- selected by reproducible pipeline;
- selected for expert review;
- evidence package;
- benchmark-supported under stated assumptions;
- candidate-selection hypothesis;
- informational result;
- requires qualified review.

## Language requiring stronger evidence

Use only when evidence supports it exactly:

- experimentally observed signal;
- independently reproduced result;
- candidate family;
- novelty-supported family;
- safety-adjusted early evidence;
- improved experiment selection.

Define context precisely.

## Language to avoid without exceptional evidence

Avoid or reject:

- drug candidate;
- safe;
- effective;
- clinically useful;
- therapy;
- cure;
- antibiotic;
- proven;
- breakthrough;
- world-first;
- AI discovered an antibiotic;
- validated by computation.

## Benchmark communication

When communicating benchmark results, state:

- benchmark name;
- dataset or source-of-truth doc;
- metric;
- cheap baselines;
- known shortcuts;
- confidence or uncertainty where available;
- whether the benchmark is exploratory, informational, gate, or deprecated;
- what the benchmark does not prove.

Do not copy stale metrics across many docs.

Link to [`METRICS_CURRENT.md`](METRICS_CURRENT.md) when possible.

## Candidate communication

When communicating a candidate or panel, state:

- proof-ladder level;
- whether evidence is dry-lab only;
- selection rule;
- novelty status;
- safety-risk status;
- release status;
- external review status;
- unsupported claims.

Do not present a top-ranked candidate as a hit.

## Negative results

Negative results should be reported where safe and interpretable.

A public report should not include only successes if failures materially affect interpretation.

Negative evidence may support:

- claim downgrade;
- benchmark revision;
- model deprecation;
- next-batch redesign;
- calibration rejection.

## Press and funder language

High-level communication may be ambitious, but it must remain grounded.

Good framing:

> OpenAMP builds open infrastructure for reproducible, safety-aware antimicrobial peptide candidate selection.

Bad framing:

> OpenAMP uses AI to discover antibiotics.

The first describes process.

The second implies evidence the project may not have.

## Agent-generated public text

Agent-generated public text requires human review before publication.

Agents should default to weaker claims and explicit caveats.

## Publication decision record

For major public claims, record:

```yaml
claim_id: stable-id
date: YYYY-MM-DD
claim_text: text
proof_ladder_level: level
supporting_artifacts: list
benchmark_source: path-or-null
safety_review: required-or-not
release_status: open | staged | restricted | internal | do-not-release
limitations: list
approved_by: role-or-name
revisit_condition: text
```

## Final standard

A public OpenAMP claim should make skeptical readers trust the project more, not because it is bold, but because it is bounded.
