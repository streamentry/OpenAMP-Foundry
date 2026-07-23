# External Review Packet

## Purpose

This document defines the standard package OpenAMP Foundry should give to qualified external reviewers before any serious claim, pilot, release, or collaboration.

A review packet is not marketing.

It is a structured invitation to find flaws.

## Prime rule

A reviewer should be able to reject the candidate panel, benchmark, claim, or release without needing private maintainer context.

## When a review packet is required

Create a review packet for:

- wet-lab-facing candidate panels;
- pre-registered pilots;
- external validation claims;
- major benchmark releases;
- model or candidate release decisions;
- safety-sensitive artifacts;
- public claims that exceed dry-lab nomination;
- collaborations with labs, funders, institutions, or public-interest groups.

## Packet types

### Candidate-panel review packet

Used when a qualified expert reviews whether a panel is worth possible testing.

### Benchmark review packet

Used when a computational reviewer attacks benchmark design and interpretation.

### Safety review packet

Used when a reviewer evaluates misuse risk, release boundaries, or claim language.

### Adoption review packet

Used when an institution, funder, or external group evaluates whether OpenAMP artifacts are useful infrastructure.

## Candidate-panel packet contents

Required:

1. Project version and commit hash.
2. Candidate manifest.
3. Evidence certificate for every candidate.
4. Scoring configuration.
5. Selection rule.
6. Baseline comparison summary.
7. Novelty audit.
8. Safety-risk summary.
9. Synthesis feasibility summary.
10. Diversity rationale.
11. Known benchmark caveats.
12. Known model blind spots.
13. Candidate rejection list where safe.
14. Unsupported-claim warning.
15. Reviewer questions.

Optional:

- external predictor comparison;
- simulation info-mode outputs;
- active-learning rationale;
- previous negative-result context;
- pre-registration draft.

## Benchmark packet contents

Required:

1. Benchmark purpose.
2. Claim gated by benchmark.
3. Dataset sources and license status.
4. Positive and negative construction.
5. Split method.
6. Leakage controls.
7. Cheap baselines.
8. Primary and secondary metrics.
9. Confidence intervals.
10. Known biases.
11. Failure interpretation.
12. Exact command and output path.
13. Current result.
14. Source-of-truth doc links.

Reviewer should be asked to find shortcut explanations.

## Safety packet contents

Required:

1. Artifact being reviewed.
2. Intended audience.
3. Intended use.
4. Disallowed use.
5. Release scope.
6. Candidate or model sensitivity.
7. Misuse scenarios.
8. Existing mitigations.
9. Remaining risks.
10. Recommended release decision.

Possible release decisions:

- open release;
- staged release;
- restricted release;
- metadata-only release;
- delayed release;
- do not release.

## Adoption packet contents

Required:

1. Project purpose.
2. First-run workflow.
3. Core artifacts.
4. Role-specific onboarding path.
5. Safety posture.
6. Benchmark status.
7. Known weaknesses.
8. Contribution path.
9. Governance and maintenance docs.
10. Open questions.

The goal is not to convince the reviewer that OpenAMP is already successful.

The goal is to show that OpenAMP is a credible substrate for serious work.

## Reviewer questionnaire

### Scientific reviewer

- Does the evidence justify the candidate-selection claim?
- Are cheap baselines adequate?
- Are novelty claims credible?
- Are safety concerns understated?
- Are weak families or model blind spots visible?
- Would you recommend possible testing, revision, or rejection?
- What would change your mind?

### Benchmark reviewer

- Could the result be explained by charge, length, hydrophobicity, or similarity?
- Is the negative set too easy?
- Are near-duplicates controlled?
- Are confidence intervals meaningful?
- Is the benchmark tied to the claim it is used for?
- Should this benchmark be exploratory, informational, gate, or deprecated?

### Safety reviewer

- Does the packet include unsafe operational detail?
- Does it release sensitive candidates or models?
- Does it enable harmful optimization?
- Does claim language exceed evidence?
- Is staged release safer?
- Is external domain review needed before publication?

### Lab/domain reviewer

- Is the panel scientifically coherent?
- Are controls and comparisons adequate at the planning level?
- Are candidate rationales interpretable?
- Are the failure modes plausible?
- Are any candidates obvious rejects?
- Does the packet help decide whether scarce experimental capacity is worth spending?

## Packet metadata

Every packet should include:

```yaml
packet_id: stable-id
packet_type: candidate-panel | benchmark | safety | adoption
created_at: YYYY-MM-DD
created_by: name-or-agent
repo_commit: git-sha
pipeline_version: version
claim_level: proof-ladder-level
review_status: draft | sent | reviewed | revised | archived
  safety_status: not-reviewed | reviewed | staged-release | restricted | rejected
```

When a reviewer outcome is recorded against a frozen PilotEvidencePackage JSON,
include `pep_sha256`, the SHA-256 of that exact canonical JSON object. Run:

```bash
PYTHONPATH=src python -m openamp_foundry.cli domain-review-outcome-check \
  --entry-json '<DRO JSON>' \
  --package-json path/to/frozen-pep.json
```

The package-aware command fails closed when the hash is missing, malformed, or
does not match the supplied package. A verified hash binds the outcome to the
package bytes only; it does not authenticate the reviewer, establish reviewer
independence, validate the science, or upgrade the proof level. Legacy outcomes
without a package file remain ID-validatable but are not package-hash verified.

## Review outcomes

Review outcome records must use real ISO calendar dates, not only the
`YYYY-MM-DD` shape. This catches malformed metadata such as `2026-02-30` at
validation time. Date validity does not authenticate the reviewer, establish
scientific correctness, or upgrade the proof level; those remain human-review
and evidence questions.

Allowed outcomes:

- approve as written;
- approve with caveats;
- revise and resubmit;
- reject claim but preserve artifact;
- reject release for safety;
- archive as negative result;
- request more evidence;
- downgrade claim level.

Rejection is useful.

A review packet that makes rejection easy is doing its job.

## Publication rule

If a public claim depends on external review, publish or summarize the review outcome where safe.

Do not imply endorsement if a reviewer only reviewed narrow scope.

Do not hide major reviewer objections.

## Final standard

A review packet should make OpenAMP look less like a pitch and more like a scientific object.

That is the point.
