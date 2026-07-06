# Agent Onboarding Playbook

## Purpose

This document tells AI agents how to work on OpenAMP Foundry without damaging scientific honesty, safety posture, or repository coherence.

Agents are welcome here only if they make the project more reproducible, more conservative where evidence is weak, and easier for qualified humans to review.

## Prime directive

**Do not make the biology look more certain than it is.**

Computational scores are triage evidence. They are not biological proof.

The lab is the judge.

## Required first reads

Before changing anything, read:

1. [`../AGENTS.md`](../AGENTS.md) — primary operating contract.
2. [`../SAFETY.md`](../SAFETY.md) — safety policy.
3. [`../RESPONSIBLE_USE.md`](../RESPONSIBLE_USE.md) — allowed and disallowed use.
4. [`../MISSION.md`](../MISSION.md) — scientific boundaries.
5. [`PROJECT_INDEX.md`](PROJECT_INDEX.md) — navigation map.
6. [`METRICS_CURRENT.md`](METRICS_CURRENT.md) — current evidence and known weaknesses.
7. [`DECISION_RULES.md`](DECISION_RULES.md) — gates and thresholds.

If there is a conflict, safety and claim discipline win.

## Agent operating loop

Use this loop for every task:

```text
1. Identify one bottleneck.
2. State the expected evidence of improvement.
3. Make the smallest change that addresses it.
4. Add or update tests.
5. Update docs if behavior or interpretation changes.
6. Run the relevant checks.
7. Record limitations and failure modes.
8. Stop before expanding scope.
```

Do not start a broad refactor unless the user explicitly requests it and the verification path is clear.

## Good agent tasks

Good agent tasks are narrow, testable, and safety-preserving.

Examples:

- add a missing schema example;
- improve a CLI error message;
- add a benchmark regression test;
- update stale documentation;
- add a cheap-baseline comparison;
- improve a report so failure modes are clearer;
- make deterministic output hashes easier to reproduce;
- add an adapter interface that fails closed;
- strengthen a safety checklist;
- turn a manual review step into a validated artifact.

## Bad agent tasks

Do not do these:

- invent wet-lab protocols;
- provide pathogen-handling instructions;
- optimize toxicity, persistence, delivery, immune evasion, or pathogenicity;
- publish unscreened candidate dumps;
- add trained generator weights;
- claim activity without assay evidence;
- change thresholds after seeing results;
- hide benchmark failures;
- add impressive simulation language without ablation evidence;
- merge broad rewrites without a clear test plan.

## Claim language rules

### Allowed before lab validation

Use these terms:

- computationally nominated candidate;
- predicted AMP-like candidate;
- dry-lab candidate;
- selected for review;
- selected by reproducible pipeline;
- candidate worth expert review;
- evidence package;
- hypothesis for qualified testing.

### Forbidden before sufficient evidence

Do not use these terms for dry-lab-only outputs:

- drug;
- cure;
- therapy;
- clinically useful;
- safe in humans;
- effective in humans;
- proven antimicrobial;
- AI-discovered antibiotic;
- breakthrough treatment.

If you are tempted to write a stronger claim, write the evidence level instead.

## Verification hierarchy

Prefer evidence in this order:

1. Tests passing in CI.
2. Reproducible benchmark outputs.
3. Frozen benchmark comparisons against cheap baselines.
4. Schema-validated artifacts.
5. External predictor or dataset comparisons with documented caveats.
6. Qualified wet-lab results.
7. Independent replication.

Do not treat a model score as high-level evidence.

## Baseline discipline

Every advanced module must have an enemy.

Common enemies:

- charge density;
- length;
- hydrophobicity;
- hydrophobic moment;
- similarity to known AMPs;
- random valid selection;
- simple selectivity proxy;
- family-stratified baseline;
- previous stable pipeline.

If your new method does not beat its cheap enemy, it may remain informational, but it should not affect ranking.

## Simulation discipline

Simulation modules are especially vulnerable to theater.

A simulation module may be useful for inspection before it is useful for ranking.

A simulation module must not affect ranking unless it passes the relevant gate and beats cheap baselines under fair comparison.

If a simulation module fails, preserve the failure.

A clean negative result is better than a fake improvement.

## Safety defaults for agents

When uncertain:

- do not release candidate lists;
- do not add biological procedures;
- do not strengthen claims;
- do not broaden scope;
- do not lower gates;
- do not add model weights;
- do not remove caveats;
- ask for human review in docs or PR notes.

The safe default is slower release, clearer evidence, and weaker public claims.

## How to choose the next task

Choose tasks by leverage, not glamour.

Use this priority order:

1. Safety bug or overclaim.
2. Broken test, broken CLI, broken docs, broken install.
3. Stale benchmark number or doc drift.
4. Missing reproducibility artifact.
5. Missing cheap-baseline comparison.
6. Missing schema validation.
7. Missing report field needed by human reviewers.
8. New feature with tests and limitations.
9. Refactor only when it unlocks one of the above.

## Do not optimize for stars

This repo should not become popular by becoming vague.

It should become important by becoming reliable.

Agents should resist language that attracts attention but weakens scientific precision.

## Required PR or commit note structure

Every nontrivial agent change should be explainable with this structure:

```md
### Change
What changed?

### Why
What bottleneck did it remove?

### Evidence
What tests, commands, or documents verify it?

### Safety impact
Does it add biological capability, release sensitive data, or change claims?

### Limitations
What does this not prove?
```

## Agent anti-patterns

### The demo-builder anti-pattern

Building a flashy pipeline without proving that it beats baselines.

### The model-worship anti-pattern

Assuming a larger model is more scientifically valid.

### The doc-hype anti-pattern

Updating language to sound more impressive than the evidence.

### The silent-threshold anti-pattern

Changing a cutoff because the result looks better.

### The biology-overreach anti-pattern

Producing wet-lab instructions or clinical language outside scope.

### The cleanup-without-tests anti-pattern

Refactoring code without preserving behavior through tests.

## What excellent agent work looks like

Excellent agent work makes a future human say:

- I can understand the repo faster.
- I can reproduce the result.
- I can see the limitations.
- I can reject the claim if the evidence is weak.
- I can safely extend this component.
- I can run the next experiment-selection loop with less ambiguity.

## Final rule

When in doubt, make the project more auditably honest.

That is the highest-leverage thing an agent can do here.
