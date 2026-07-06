# Leakage Audit Checklist

OpenAMP Foundry should treat leakage as a first-order evidence risk.

This checklist helps reviewers and contributors inspect whether a benchmark, scorer, dataset, or selection step is accidentally learning from information that would not be available in a real prospective decision.

This document is about evidence hygiene only. It does not add biological protocols, candidate-generation instructions, or optimization objectives.

## When to use

Use this checklist when a PR adds or changes:

- benchmark data;
- train/test splits;
- scoring or ranking logic;
- external predictor outputs;
- model cards;
- evidence certificates;
- shortlist or panel-selection rules;
- claims about improved performance.

## Leakage questions

A submission should answer the relevant questions below.

1. **Duplicate leakage:** Are near-duplicate records split across evaluation boundaries?
2. **Family leakage:** Are closely related records split in a way that makes performance look stronger than prospective use?
3. **Label leakage:** Does any feature encode the target, source label, or curation decision?
4. **Time leakage:** Does the evaluation use information that would not have existed at the decision date?
5. **Source leakage:** Are records from the same database, paper, lab, or preprocessing pipeline appearing in both comparison sides in a misleading way?
6. **Selection leakage:** Were thresholds, filters, or candidate groups chosen after seeing evaluation results?
7. **Metric leakage:** Was the primary metric changed after observing which metric looked best?
8. **Review leakage:** Did human review influence the evaluation set before performance was reported?
9. **Novelty leakage:** Does a novelty check use references that include the object being evaluated or close derivatives?
10. **Generated-artifact leakage:** Are generated files reused as if they were independent evidence?

## Minimum audit note

```markdown
## Leakage audit

**Artifact:** Benchmark, scorer, dataset, report, or selection step.

**Evaluation boundary:** What is supposed to be independent from what?

**Most plausible leakage path:** One concrete path.

**Check performed:** Exact check, command, review method, or reason not checked.

**Result:** no obvious leakage found | leakage found | inconclusive | not applicable.

**Decision impact:** no change | claim narrowed | benchmark blocked | scorer exploratory | follow-up required.
```

## Reviewer guidance

A reviewer does not need to prove leakage to ask for this audit. The submitter must show why the result is not obviously inflated by a preventable boundary failure.

If the audit is inconclusive, the claim can still be useful, but it should not be promoted beyond the strength of the audit.

## Agent guidance

An agent should identify the evaluation boundary before reporting performance.

If the boundary cannot be named, the result is not ready to carry a benchmark or ranking claim.

## Acceptance test

A leakage audit is useful when a skeptical reviewer can say:

> I understand what was supposed to be independent, the most plausible way independence could fail, and what check was performed.

If those three facts are missing, the result is not yet trustworthy.
