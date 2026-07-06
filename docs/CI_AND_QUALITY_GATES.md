# CI and Quality Gates

## Purpose

This document defines how OpenAMP Foundry should use tests, linting, schemas, benchmarks, claim checks, and release checks to keep the project trustworthy.

CI is not only engineering hygiene here. It is part of scientific governance.

## Prime rule

**A gate should block the easiest way to fool the project.**

If a gate only checks style but not meaning, it is incomplete.

## Gate classes

| Gate class | Purpose | Examples |
|---|---|---|
| Engineering gates | Prevent broken code. | tests, lint, type checks, packaging. |
| Artifact gates | Prevent invalid outputs. | schema validation, manifest checks, version checks. |
| Benchmark gates | Prevent scientific regression. | metric drift, cheap-baseline comparisons, leakage checks. |
| Claim gates | Prevent overclaiming. | proof-ladder scan, forbidden phrase scan. |
| Safety gates | Prevent unsafe scope or release. | release status, policy checks, review labels. |
| Agent gates | Prevent agent drift. | agent-safe scope, docs index update, PR template fields. |

## Minimum CI expectations

A healthy baseline CI should include:

- unit tests;
- lint checks;
- schema validation for examples;
- smoke test for demo workflow;
- internal doc-link check;
- benchmark gate or benchmark smoke test;
- forbidden-claim scan for public docs;
- check that new core docs appear in `docs/PROJECT_INDEX.md`.

## Quality gate philosophy

A gate should be:

- deterministic;
- cheap enough for routine use;
- clear when it fails;
- tied to a documented rule;
- resistant to silent bypass;
- useful to humans and agents.

A flaky gate is worse than no gate because it teaches contributors to ignore gates.

## Engineering gates

Engineering gates should answer:

- Does the package install?
- Do tests pass?
- Does lint pass?
- Do example commands still work?
- Are outputs deterministic where required?
- Are error messages actionable?

## Artifact gates

Artifact gates should answer:

- Does the artifact match schema?
- Does it include artifact version?
- Does it include provenance?
- Does it include proof-ladder level where needed?
- Does it include release status?
- Does it avoid unsupported claim fields?
- Is it compatible with previous versions?

## Benchmark gates

Benchmark gates should answer:

- Did a core metric regress?
- Did a cheap baseline beat the advanced method?
- Did leakage appear?
- Did a benchmark card change?
- Are confidence intervals or known caveats recorded?
- Does `docs/METRICS_CURRENT.md` match current behavior?

Benchmark gates should not be silently relaxed.

If a threshold changes, require a decision record.

## Claim gates

Claim gates should scan public-facing text for risky wording.

Flag phrases such as:

- drug candidate;
- safe;
- clinically useful;
- proven;
- breakthrough;
- AI discovered an antibiotic;
- validated by computation.

A scan is not a substitute for review, but it catches obvious drift.

## Safety gates

Safety gates should check whether changed files require review.

Examples:

| Changed area | Required action |
|---|---|
| `SAFETY.md` | Safety review. |
| `MODEL_RELEASE_POLICY.md` | Safety/release review. |
| candidate artifacts | Release review. |
| non-toy data | Data and safety review. |
| external-facing review docs | Domain/safety review. |
| benchmark thresholds | Benchmark governance review. |
| calibration policy | Human review and decision record. |

## Agent gates

Agent-generated changes should verify:

- scope stayed narrow;
- PR template was completed;
- proof-ladder level is explicit where claims exist;
- no safety-sensitive file changed without review;
- docs index updated when important docs were added;
- limitations are stated.

## Local command targets to add over time

Future useful commands:

```text
make docs-check       # internal links, source-of-truth references, index coverage
make claim-check      # forbidden or risky claim language
make artifact-check   # schema/version/release-status validation
make release-check    # release checklist automation
make agent-check      # safe-scope and agent PR checks
make data-check       # dataset-card and license metadata validation
make model-check      # model-card and release-status validation
```

These should start as advisory checks before becoming hard gates.

## Failure reports

A gate failure should include:

- failing gate name;
- exact file or artifact;
- expected condition;
- observed condition;
- likely fix;
- source-of-truth doc.

A failure that only says “failed” wastes contributor time.

## Gate promotion policy

A check should move through stages:

```text
manual checklist
  -> advisory script
  -> CI warning
  -> required CI gate
```

Do not make a new gate mandatory until it is stable and clearly useful.

## Final standard

OpenAMP’s quality gates should make the project safer, more reproducible, and harder to fool without making useful contribution miserable.
