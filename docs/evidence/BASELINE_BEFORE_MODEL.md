# Baseline Before Model Standard

OpenAMP Foundry should require every new predictive, ranking, or screening component to beat a cheap transparent baseline before it earns trust.

This document defines the minimum comparison standard for adding or promoting model-like components.

It is intentionally conservative. It does not define new biological objectives, candidate-generation instructions, wet-lab methods, or optimization recipes. It only defines how to compare a proposed component against simpler alternatives.

## Why this matters

Model complexity is seductive. A new model can look like progress while adding little more than opacity, variance, maintenance cost, or hidden leakage.

For a safety-first foundry, the question is not:

> Is the new model impressive?

The question is:

> Does the new component improve the decision that the foundry must make, compared with the cheapest transparent baseline available?

If the answer is no, the component should stay exploratory.

## Required baseline comparison

A PR that adds or promotes a predictive, scoring, ranking, or screening component should include a baseline comparison unless it is explicitly marked exploratory.

The comparison should answer:

1. **Decision target:** What decision does this component change?
2. **Cheap baseline:** What simple rule, heuristic, or existing scorer is it compared against?
3. **Metric:** Which metric decides whether the component is better?
4. **Data version:** Which dataset, split, or benchmark slice was used?
5. **Leakage check:** What obvious leakage path was ruled out?
6. **Failure slice:** Where did the new component perform worse or add no value?
7. **Operational effect:** What changes in shortlist, review packet, threshold, or confidence boundary?

If those questions cannot be answered, the component can still exist, but it should not carry decision weight.

## Minimum record

Use this record in benchmark notes, model cards, evidence docs, or PR descriptions:

```markdown
## Baseline comparison

**Component:** Name of model, scorer, heuristic, adapter, or selection layer.

**Decision target:** What decision this component is supposed to improve.

**Baseline:** The cheapest transparent comparator.

**Benchmark slice:** Dataset version, split, controls, and relevant filters.

**Primary metric:** The metric that determines whether this is better.

**Secondary checks:** Calibration, robustness, subgroup or slice behavior, runtime, maintenance cost.

**Result:** Better | tied | worse | inconclusive.

**Failure slices:** Where the component underperformed, overfit, or added no practical value.

**Decision impact:** exploratory only | lower weight | equal weight | promoted | blocked.

**Re-run command or artifact:** Link to command, run manifest, report, or certificate.
```

## Promotion rule

A component should be promoted only when it improves a declared decision under a declared metric and does not introduce unacceptable safety, leakage, reproducibility, or maintenance risk.

A component should remain exploratory when:

- it is better only on a cherry-picked slice;
- it improves a proxy metric but does not change any useful decision;
- it cannot be reproduced from repository artifacts;
- it is not compared to a cheap baseline;
- it performs worse on a known failure slice;
- it adds opacity without a measurable benefit;
- it makes shortlist selection harder to audit.

## Reviewer rule

Reviewers should ask for a baseline comparison before accepting model-like complexity as decision-relevant.

The burden is on the PR to show that complexity buys something. The reviewer does not need to prove that the model is bad.

## Agent rule

An agent proposing a new component should first identify the current cheap baseline.

The agent should answer:

1. What is the simplest thing that might work?
2. What decision would change if my component is better?
3. What would make my component stay exploratory?
4. Which failure slice am I most likely to hide by accident?
5. How can a reviewer reproduce my comparison?

If the answer is unclear, the agent should propose a benchmark task before proposing the component.

## Anti-patterns

Avoid:

- comparing only against no model;
- reporting only aggregate performance;
- hiding weak slices;
- promoting a component because it is newer;
- treating benchmark gain as biological proof;
- changing metrics after seeing results;
- adding a model that cannot be reproduced by maintainers.

## Acceptance test

A baseline comparison is useful when a skeptical reviewer can say:

> I understand what simple alternative this beat, what decision it improves, where it fails, and what artifact reproduces the comparison.

If the comparison cannot meet that bar, the component should not become load-bearing.
