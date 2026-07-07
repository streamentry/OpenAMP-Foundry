# Expert Review Pack

## Status

**Template / safe review standard. Not a candidate dump. Not a wet-lab protocol.**

This document defines what an OpenAMP expert review pack should contain before a qualified microbiology, peptide science, toxicology, computational biology, safety, or institutional reviewer evaluates a candidate panel or project claim.

It replaces earlier panel-specific review drafts that included operational or overly specific candidate details.

## Purpose

The expert review pack should help a qualified reviewer answer:

> Is this computational candidate-selection package credible enough to justify further review, revision, rejection, or possible qualified external testing?

It should not persuade the reviewer with confidence.

It should make the evidence, weaknesses, baselines, safety boundaries, and unsupported claims easy to inspect.

## Prime rule

**A good expert review pack makes rejection easy.**

If the reviewer cannot reject a candidate, panel, benchmark, or claim from the information provided, the pack is not review-ready.

## Claim boundary

Before qualified experimental evidence, all candidates remain computationally nominated.

Allowed language:

- computationally nominated candidate;
- dry-lab candidate;
- selected for expert review;
- selected by reproducible pipeline;
- evidence package;
- candidate panel hypothesis.

Forbidden language before sufficient evidence:

- active antimicrobial;
- safe;
- drug candidate;
- therapeutic;
- clinical;
- proven;
- AI-discovered antibiotic.

Use [`PROOF_LADDER.md`](../evidence/PROOF_LADDER.md) for evidence levels.

## Required packet structure

```text
expert_review_pack/
  README.md
  packet_metadata.yaml
  candidate_manifest.json
  evidence_certificates/
  selection_rule.md
  benchmark_summary.md
  baseline_comparison.md
  novelty_summary.md
  safety_risk_summary.md
  synthesis_feasibility_summary.md
  diversity_rationale.md
  model_blind_spots.md
  unsupported_claims.md
  reviewer_questionnaire.md
  safety_release_review.md
```

## Packet metadata

Every review pack should include:

```yaml
packet_id: stable-id
packet_type: expert-review
created_at: YYYY-MM-DD
created_by: maintainer-or-agent
repo_commit: git-sha
pipeline_version: version
candidate_manifest: path-or-restricted-reference
evidence_certificate_dir: path
claim_level: proof-ladder-level
release_status: internal | review-only | staged | public-summary | do-not-release
review_status: draft | sent | reviewed | revised | archived
```

## Candidate manifest standard

The manifest should describe the panel without becoming an unsafe public candidate dump.

Fields should include:

- candidate ID;
- sequence hash or safe sequence reference;
- panel role;
- scaffold family or cluster;
- structural class if available;
- proof-ladder level;
- key score summary;
- novelty label;
- safety-risk label;
- synthesis-feasibility label;
- baseline caveat;
- release status;
- evidence-certificate path.

Full sequences should be included only when release review allows it.

## Selection-method summary

The pack should explain:

- input candidate source;
- validation filters;
- feature extraction;
- scoring components;
- ensemble or selection logic;
- novelty checks;
- safety-risk filters;
- diversity selection;
- human review gates;
- known limitations.

The explanation should distinguish current implemented behavior from future roadmap ideas.

## Benchmark summary

The benchmark summary should include:

- current source-of-truth metrics from [`METRICS_CURRENT.md`](../evidence/METRICS_CURRENT.md);
- benchmark commands from [`BENCHMARKING.md`](../evidence/BENCHMARKING.md);
- benchmark status from [`BENCHMARK_GOVERNANCE.md`](../evidence/BENCHMARK_GOVERNANCE.md);
- cheap baselines;
- confidence intervals where available;
- known shortcuts;
- known blind spots;
- whether the benchmark gates any claim.

Do not copy stale metrics into this file unless they are explicitly dated and sourced.

## Baseline comparison

A review pack should answer:

> What simple explanation might make OpenAMP look better than it is?

At minimum, review whether selection could be explained by:

- charge;
- length;
- hydrophobicity;
- amphipathicity;
- similarity to known AMPs;
- ranker bias toward canonical helical AMPs;
- duplicate or near-duplicate leakage;
- weak negative-set construction.

If the pack lacks baseline comparison, it is exploratory only.

## Novelty summary

The novelty summary should include:

- reference sets checked;
- version/date/hash of reference sets;
- similarity method;
- nearest-neighbor summary where safe;
- novelty labels;
- known reference gaps;
- whether any candidates are controls, derivatives, close relatives, or plausible novel hypotheses.

A candidate is not novel merely because it is absent from one reference file.

## Safety-risk summary

The safety-risk summary should include:

- dry-lab safety flags;
- model blind spots;
- whether any candidates should be rejected from the panel;
- whether release should be restricted;
- whether safety review is required before public artifacts;
- unsupported safety claims.

OpenAMP dry-lab safety scores do not prove biological safety.

## Synthesis-feasibility summary

The pack may include non-operational feasibility flags for qualified review.

It should not provide synthesis procedures, storage instructions, assay instructions, or experimental recipes.

## Diversity rationale

A useful panel should explain why each candidate is present.

Possible reasons:

- high-confidence lead;
- baseline challenger;
- known-family control;
- uncertainty probe;
- diversity probe;
- underrepresented structural class;
- safety-boundary check;
- novelty probe.

A panel should not be only the top-k ranking.

## Reviewer questionnaire

### Scientific credibility

1. Is the selection logic credible for the stated goal?
2. Are cheap baselines adequate?
3. Are the benchmark caveats serious enough to downgrade the claim?
4. Are model blind spots visible?
5. Are any candidates obvious rejects?
6. Does the panel ask a coherent experimental question?

### Novelty

1. Are novelty labels justified?
2. Are references broad enough?
3. Are any candidates near-duplicates or derivatives?
4. Are novelty claims conservative enough?

### Safety and release

1. Does the pack include unsafe operational detail?
2. Does it release sensitive candidates without review?
3. Does it enable harmful optimization?
4. Does it imply safety without biological evidence?
5. Should release be staged, restricted, summarized, or rejected?

### External testing readiness

1. Are candidate roles clear?
2. Are success/failure criteria pre-registered?
3. Are baseline panels included where feasible?
4. Is result intake defined?
5. Is the claim level clear?
6. Is this ready for possible qualified external testing, revision, or rejection?

## Review outcomes

Allowed outcomes:

- approve for further review;
- approve with caveats;
- revise candidate panel;
- downgrade novelty claim;
- require better baseline comparison;
- require safety review;
- reject candidate(s);
- reject pilot readiness;
- archive as negative or insufficient evidence;
- do not release.

Rejection should be documented and treated as useful evidence.

## Publication boundary

If an expert review pack supports a public statement, publish only the claim level justified by the evidence.

Do not imply that expert review equals experimental validation.

Do not imply that selection for testing equals expected efficacy.

Do not imply that a reviewer endorsed claims outside their review scope.

## Relationship to other docs

- [`EXTERNAL_REVIEW_PACKET.md`](EXTERNAL_REVIEW_PACKET.md) — broader packet standard.
- [`WET_LAB_HANDOFF.md`](WET_LAB_HANDOFF.md) — safe expert-review handoff guide.
- [`PRE_REGISTERED_PILOT_TEMPLATE.md`](PRE_REGISTERED_PILOT_TEMPLATE.md) — pilot planning template.
- [`PROOF_LADDER.md`](../evidence/PROOF_LADDER.md) — claim levels.
- [`BENCHMARK_GOVERNANCE.md`](../evidence/BENCHMARK_GOVERNANCE.md) — benchmark lifecycle.
- [`MODEL_RELEASE_POLICY.md`](../) — release boundaries.

## Final standard

An expert review pack should make OpenAMP more credible by making its weaknesses easier to see.

That is how serious scientific infrastructure earns trust.
