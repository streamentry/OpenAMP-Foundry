# Benchmark Slice Register

OpenAMP Foundry should track benchmark slices explicitly.

Aggregate benchmark performance is rarely enough. A component can look strong overall while failing on the slice that matters most for safe selection, novelty, feasibility, or review readiness.

This register defines how to name and preserve benchmark slices without adding biological protocols, candidate-generation instructions, or optimization objectives.

## Why this matters

Benchmarks become misleading when failure slices are unnamed.

If the repo only remembers aggregate results, future contributors cannot tell whether a change improves robust selection or merely shifts performance across hidden subgroups.

Named slices make benchmark claims harder to launder through averages.

## What is a benchmark slice?

A benchmark slice is a declared subset of an evaluation used to inspect behavior under a meaningful boundary.

Examples of slice dimensions:

- source database or curation path;
- dataset version;
- novelty band;
- feasibility band;
- safety-review band;
- sequence length band;
- known-control group;
- external-predictor availability;
- review-readiness level;
- time or reference-version boundary.

A slice should exist because it tests a failure mode, not because it makes a result look better.

## Minimum slice record

```markdown
## Benchmark slice

**Slice ID:** Stable identifier.

**Purpose:** What failure mode or claim boundary this slice tests.

**Inclusion rule:** How records enter the slice.

**Exclusion rule:** How records are excluded.

**Dataset or reference version:** Version, commit, date, or artifact.

**Primary metric:** Metric used for this slice.

**Expected behavior:** What should a useful component do on this slice?

**Known caveat:** Why this slice could mislead.

**Owner:** Maintainer, reviewer, or workstream responsible for updates.
```

## Reviewer guidance

Reviewers should ask for a slice record when aggregate performance hides a meaningful boundary.

A slice does not need to be permanent. It should remain while it captures a live failure mode or claim boundary.

## Agent guidance

Agents should not invent slices after seeing which ones look favorable.

An agent proposing a new slice should state the failure mode first, then define the inclusion rule.

## Anti-patterns

Avoid:

- creating slices only after observing results;
- reporting only the best slice;
- changing slice definitions without recording why;
- comparing components across different slice definitions;
- using tiny slices without marking uncertainty;
- hiding weak slices behind aggregate improvement.

## Acceptance test

A benchmark slice is useful when a reviewer can answer:

1. What failure mode does this slice test?
2. How are records included and excluded?
3. Which claim boundary depends on it?
4. What caveat travels with the result?

If those answers are missing, the slice is not benchmark governance. It is decoration.
