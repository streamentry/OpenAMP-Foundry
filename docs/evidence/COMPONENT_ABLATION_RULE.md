# Component Ablation Rule

OpenAMP Foundry should not accept added complexity unless the useful part of that complexity can be isolated.

This rule defines when a new scoring, ranking, filtering, adapter, report, or selection component needs an ablation note.

It is an evidence-governance document only. It does not add biological protocols, candidate-generation instructions, or optimization objectives.

## Why this matters

A pipeline can improve after a change for the wrong reason.

The useful gain may come from a small preprocessing fix, a stricter filter, a changed threshold, a changed dataset, or random variation rather than the new component being promoted.

Ablation protects the repo from rewarding complexity that does not carry its own weight.

## When ablation is required

Add an ablation note when a PR:

- adds a new scoring component;
- changes score weights;
- adds an external predictor or adapter;
- changes ranking or selection behavior;
- changes filters that affect downstream evaluation;
- claims improvement from a multi-part change;
- promotes exploratory logic into decision-relevant logic.

Ablation can be skipped when the change is documentation-only, clearly mechanical, or explicitly not decision-relevant.

## Minimum ablation note

```markdown
## Component ablation

**Component:** What was added or changed?

**Decision affected:** Ranking, filtering, evidence certificate, handoff packet, benchmark, or report.

**Baseline condition:** What happens without this component?

**Component-only effect:** What changes when only this component is added?

**Interactions:** Which other changes might explain the result?

**Failure slice:** Where the component does not help or makes the result worse.

**Decision impact:** exploratory only | lower weight | keep | promote | remove.

**Reproduction artifact:** Command, report, run manifest, or reason not run.
```

## Reviewer guidance

Reviewers should ask whether the claimed improvement belongs to the component or to something else in the PR.

If the PR cannot isolate the effect, the component may still be merged as exploratory, but it should not become load-bearing.

## Agent guidance

Agents should avoid bundling multiple decision-relevant changes in one PR unless they include an ablation note.

If an agent cannot isolate which part helped, it should split the PR or lower the proposed decision impact.

## Anti-patterns

Avoid:

- adding a component and changing the dataset in the same claim without separation;
- reporting only the final pipeline result;
- promoting a component because the combined PR improved;
- ignoring slices where the component worsens behavior;
- treating complexity as evidence.

## Acceptance test

An ablation note is useful when a reviewer can answer:

1. What changed without the component?
2. What changed because of the component alone?
3. Where did it fail?
4. Should it remain exploratory or become decision-relevant?

If those answers are missing, the complexity is not yet justified.
