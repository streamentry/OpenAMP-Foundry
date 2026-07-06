# Maintainer Guide

## Purpose

This guide defines how maintainers should protect OpenAMP Foundry as it grows.

The maintainer job is not to make the project look successful.

The maintainer job is to make the project trustworthy enough that success, failure, and uncertainty can all be interpreted correctly.

## Maintainer mandate

Maintain OpenAMP as a safe, reproducible, evidence-first public-good infrastructure project for antimicrobial peptide experiment selection.

That means:

- protect safety boundaries;
- protect claim discipline;
- protect benchmark honesty;
- protect contributor experience;
- protect external reviewability;
- protect negative results;
- protect schema and artifact stability;
- protect the ability to say “we were wrong.”

## The maintainer hierarchy of values

When values conflict, use this order:

1. Safety.
2. Scientific honesty.
3. Reproducibility.
4. External auditability.
5. Contributor speed.
6. Feature breadth.
7. Public attention.

Attention is last.

## Maintainer review checklist

Before merging a meaningful change, answer:

### Scope

- Is the change narrow enough to review?
- Does it solve a real bottleneck?
- Does it avoid broad refactors without need?

### Evidence

- Are tests added or updated?
- Are benchmark changes documented?
- Are cheap baselines included where relevant?
- Are limitations stated?
- Is the source-of-truth metric updated if behavior changes?

### Safety

- Does this add biological capability?
- Does this publish candidate sequences or sensitive artifacts?
- Does this change release boundaries?
- Does this affect wet-lab-facing artifacts?
- Does this need human safety review?

### Claims

- Does any wording exceed the evidence level?
- Does the change imply biological proof from computation?
- Does it use forbidden terms from the claim policy?
- Does it link to the proof ladder where appropriate?

### Maintainability

- Will a future agent or human understand this?
- Are docs updated?
- Are schemas versioned where needed?
- Are errors explicit?
- Is behavior deterministic?

## Merge classes

### Class A — Safe documentation or small bug fix

Examples:

- typo fix;
- broken link;
- clearer command example;
- small error message fix;
- test-only regression for existing behavior.

Review bar: basic correctness and no claim/safety regression.

### Class B — Infrastructure change

Examples:

- schema updates;
- report changes;
- CLI behavior;
- deterministic output;
- adapter scaffolding;
- benchmark script infrastructure.

Review bar: tests, docs, compatibility note, safety impact note.

### Class C — Scientific behavior change

Examples:

- scoring changes;
- selection logic;
- benchmark thresholds;
- calibration logic;
- active-learning behavior;
- simulation integration.

Review bar: tests, benchmark comparison, cheap baseline, source-of-truth docs, human review.

### Class D — Safety-sensitive change

Examples:

- model release;
- candidate release;
- wet-lab-facing docs;
- safety policy;
- harmful-capability risk;
- external collaboration package.

Review bar: safety review mandatory, conservative release, no automerge.

## When to say no

Reject or request changes when:

- a model affects ranking without beating cheap baselines;
- a benchmark threshold moves without a decision record;
- language overclaims evidence;
- wet-lab operational details are added;
- candidate lists are published without review;
- safety caveats are removed;
- negative results are hidden;
- a change makes outputs less reproducible;
- a contribution adds complexity without strategic leverage.

A polite no is less useful than a clear no.

## Handling benchmark regressions

When a benchmark regresses:

1. Do not hide it.
2. Record the metric, commit, and command.
3. Identify whether the regression is expected.
4. Decide which claim must be downgraded.
5. If the regression is acceptable, document why.
6. If not acceptable, block the merge or revert.

A regression may reveal that an earlier claim was too strong. That is useful.

## Handling negative wet-lab results

Negative results should not be treated as reputation damage.

Maintainers should ask:

- Was the candidate selection pre-registered?
- Were baselines included?
- Were controls interpretable?
- Is the result safe to publish?
- Does it falsify a scorer, feature, or selection rule?
- Does the recalibration gate allow an update?
- What should the next batch learn?

A clean negative result can be one of the project’s most valuable artifacts.

## Handling positive wet-lab results

Positive results are more dangerous than negative results because they invite overclaiming.

Before any public claim:

1. Map the result to [`PROOF_LADDER.md`](PROOF_LADDER.md).
2. Check novelty carefully.
3. Check safety-adjusted interpretation.
4. Compare against baselines.
5. State exact tested context.
6. Preserve failed candidates.
7. Require external review before strong language.

Do not convert a signal into a story faster than the evidence allows.

## Handling agents

Agents can be valuable contributors if tasks are narrow and verifiable.

Maintainers should give agents:

- one bottleneck;
- clear files to inspect;
- allowed scope;
- required checks;
- claim boundaries;
- stop conditions.

Agents should not autonomously change:

- safety policy;
- candidate release policy;
- benchmark thresholds;
- wet-lab-facing docs;
- model release;
- calibration policy;
- claim language for results.

Those changes require explicit human review.

## Release discipline

Every release should include:

- version tag;
- key changes;
- benchmark status;
- known regressions;
- safety-impact note;
- schema changes;
- claim changes;
- deprecated modules;
- next bottleneck.

A release should not merely say what improved. It should say what is still not proven.

## Governance memory

Important decisions should leave records.

Record:

- benchmark threshold changes;
- safety policy changes;
- model release decisions;
- candidate publication decisions;
- wet-lab collaboration decisions;
- recalibration decisions;
- major claim wording changes.

The project should be understandable from history, not oral tradition.

## Maintainer anti-patterns

### Hero-maintainer bottleneck

One person knows why everything matters.

Fix: document decisions and task maps.

### Hype-preserving review

Rejecting negative results because they weaken the story.

Fix: treat negative results as assets.

### Metric theater

Adding more metrics without stronger interpretation.

Fix: tie each benchmark to a claim or kill rule.

### Safety paperwork

Keeping safety in docs but not in defaults, gates, or review process.

Fix: make safety operational.

### Agent drift

Letting agents expand scope because they can generate plausible text.

Fix: enforce agent onboarding, proof ladder, and human review.

## Maintainer oath

I will not make OpenAMP look more certain than it is.

I will preserve failures that teach the project something.

I will block unsafe or unsupported claims even when they are exciting.

I will prefer a slower trustworthy release over a faster fragile one.

I will make the repo easier for the next serious human or agent to inspect.
