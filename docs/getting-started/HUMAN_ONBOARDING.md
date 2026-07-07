# Human Onboarding Guide

## Purpose

This guide helps humans become useful quickly without weakening the project’s scientific or safety standards.

OpenAMP Foundry is not a normal software repo. It sits near biology, safety, and scientific claims. Contributions are welcome, but they must improve evidence, reproducibility, decision quality, or safe usability.

## The project in one paragraph

OpenAMP Foundry is a safety-first dry-lab system for antimicrobial peptide candidate triage. It ranks and documents computationally nominated candidates, challenges them with baselines, checks novelty and safety-related risks, produces evidence certificates, and prepares reviewable artifacts for qualified experts. The long-term ambition is to become a wet-lab compression engine that helps scientists choose fewer, better experiments and learn from the results.

## What you should believe before contributing

You should believe that:

- biological prediction is not biological proof;
- simple baselines are dangerous enemies, not trivial formalities;
- negative results are scientific assets;
- safety is part of architecture;
- reproducibility is more valuable than impressiveness;
- human domain review remains mandatory;
- a small, honest result beats a large, unsupported claim.

If you want to make dramatic claims faster than the evidence supports, this is the wrong repo.

## First 30 minutes

1. Read [`README.md`](../README.md).
2. Read [`SAFETY.md`](../).
3. Run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make demo
make test
```

4. Open the generated outputs and inspect what the pipeline actually produces.
5. Read [`docs/evidence/METRICS_CURRENT.md`](../evidence/METRICS_CURRENT.md) before trusting any performance claim.

## First two hours

Read the docs that match your role.

### Engineer path

- [`docs/engineering/ARCHITECTURE.md`](../engineering/ARCHITECTURE.md)
- [`CONTRIBUTING.md`](../)
- [`docs/evidence/BENCHMARKING.md`](../evidence/BENCHMARKING.md)
- [`docs/evidence/DECISION_RULES.md`](../evidence/DECISION_RULES.md)

Then look for a small issue in CLI ergonomics, tests, reports, schemas, or doc consistency.

### Scientist path

- [`VISION.md`](../)
- [`GOAL.md`](../)
- [`docs/evidence/PROOF_LADDER.md`](../evidence/PROOF_LADDER.md)
- [`docs/evidence/METRICS_CURRENT.md`](../evidence/METRICS_CURRENT.md)
- [`docs/evidence/BENCHMARKING.md`](../evidence/BENCHMARKING.md)

Then look for a weak benchmark, missing baseline, leakage risk, uncontrolled comparison, or overclaim.

### Lab-review path

- [`docs/review/WET_LAB_HANDOFF.md`](../review/WET_LAB_HANDOFF.md)
- [`docs/review/COLLABORATION_PLAYBOOK.md`](../review/COLLABORATION_PLAYBOOK.md)
- [`docs/evidence/PROOF_LADDER.md`](../evidence/PROOF_LADDER.md)
- [`RESPONSIBLE_USE.md`](../)

Then review whether the evidence package would help a qualified scientist decide whether a small assay batch is worth considering.

### Safety path

- [`SAFETY.md`](../)
- [`RESPONSIBLE_USE.md`](../)
- [`MODEL_RELEASE_POLICY.md`](../)
- [`docs/evidence/DECISION_RULES.md`](../evidence/DECISION_RULES.md)

Then look for release risk, overclaiming, unsafe defaults, unclear boundaries, or missing human-review gates.

## First contribution menu

### Safe beginner contributions

- Improve one unclear doc paragraph.
- Add a missing link to the project index.
- Improve one CLI help string.
- Add a small test for a known edge case.
- Add a schema-valid example artifact.
- Improve one report warning.
- Add one doc consistency check.

### Medium contributions

- Add a cheap-baseline comparison.
- Add a benchmark caveat to the right source-of-truth doc.
- Improve error handling in a pipeline step.
- Add a new adapter that fails closed and has tests.
- Improve candidate evidence certificate readability.
- Add a role-specific onboarding path.

### Advanced contributions

- Add a leakage-resistant benchmark.
- Improve family-stratified evaluation.
- Create an external predictor adapter with fair comparison.
- Strengthen calibration and active-learning evaluation.
- Prepare a pre-registered pilot package for qualified review.
- Build infrastructure for safe negative-result publication.

## Contribution standards

Every meaningful contribution should answer five questions.

### 1. What bottleneck does this remove?

The answer should be concrete.

Weak: “Improves discovery.”

Strong: “Adds a charge-matched baseline so the activity scorer cannot appear strong merely by ranking cationic peptides.”

### 2. What evidence shows it worked?

Use tests, benchmarks, schema validation, deterministic output, or reviewable docs.

Do not use confidence as evidence.

### 3. What does it not prove?

Every improvement should have a boundary.

A better AUROC on a dry-lab benchmark does not prove antimicrobial activity.

A simulation module does not prove mechanism.

A candidate certificate does not prove safety.

### 4. What is the safety impact?

Say whether the change adds biological capability, releases sequences, changes claim language, modifies safety filters, or affects candidate selection.

### 5. What future work becomes easier?

Good infrastructure makes the next useful action easier.

## The OpenAMP standard for “done”

A change is not done when it works once.

It is done when:

- tests cover the new behavior;
- docs reflect the new behavior;
- safety impact is explicit;
- failure modes are recorded;
- benchmarks or baselines are updated if relevant;
- outputs are reproducible;
- a future human or agent can continue without private context.

## How to avoid bad contributions

### Do not add hidden magic

A black-box improvement without provenance, tests, and limitations is not helpful.

### Do not add unsupported confidence

If you write “validated,” specify validated by what.

If the answer is only computational, say computational.

### Do not make the repo harder to audit

Avoid unexplained dependencies, silent downloads, hidden randomness, unversioned data, and implicit thresholds.

### Do not optimize the wrong objective

Activity without safety, novelty, and follow-up value is not the project’s goal.

### Do not treat safety as a blocker to route around

Safety is part of why the project can be open.

## How review works

Review should be stricter for changes that affect:

- candidate ranking;
- safety scores;
- data sources;
- model release;
- candidate publication;
- wet-lab-facing artifacts;
- claim language;
- benchmark thresholds;
- calibration decisions.

A typo fix does not need the same scrutiny as a new scorer.

A new scorer should be attacked with baselines before it earns trust.

## What expert review should look for

Domain experts should ask:

- Are the candidates biologically plausible for the stated goal?
- Are the controls appropriate?
- Are novelty claims credible?
- Are safety concerns understated?
- Are assay endpoints interpretable?
- Are claims weaker than the evidence?
- Would this package help decide whether to spend limited lab capacity?

## What engineering review should look for

Engineers should ask:

- Is the output deterministic?
- Are schemas validated?
- Are errors explicit?
- Does the CLI fail safely?
- Are data paths clear?
- Are tests meaningful?
- Are docs updated?
- Is the new dependency justified?

## What safety review should look for

Safety reviewers should ask:

- Does this increase misuse capability?
- Does this publish sensitive candidates or instructions?
- Does this encourage harmful optimization?
- Does this blur computational and experimental evidence?
- Does this need staged release or external review?
- Does this create incentives for unsafe forks?

## How to become a core contributor

Core contributors should repeatedly demonstrate:

- accuracy over excitement;
- tests over claims;
- safety over speed;
- willingness to publish negative results;
- respect for domain expertise;
- ability to make the repo easier for others;
- comfort attacking their own favorite idea with baselines.

The best contributors are not those who make OpenAMP look strongest.

They are those who make OpenAMP hardest to fool.

## The contribution north star

Leave the repo more trustworthy than you found it.

That is the standard.
