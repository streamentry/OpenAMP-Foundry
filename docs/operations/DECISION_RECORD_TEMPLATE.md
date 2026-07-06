# Decision Record Template

## Purpose

Use this template for important project decisions that should remain understandable after the original discussion is gone.

Decision records are required for safety-sensitive, benchmark-sensitive, release-sensitive, calibration-sensitive, or claim-sensitive changes.

## Template

```md
# Decision Record: <short title>

## Metadata

- Decision ID: DR-YYYY-MM-DD-short-name
- Date: YYYY-MM-DD
- Status: proposed | accepted | rejected | superseded
- Decision class: A | B | C | D
- Owner: name-or-role
- Reviewers: names-or-roles
- Related PRs/issues: links

## Context

What problem or choice required a decision?

## Options considered

### Option 1

Description.

Pros:

- ...

Cons:

- ...

### Option 2

Description.

Pros:

- ...

Cons:

- ...

## Evidence

List evidence used:

- tests;
- benchmarks;
- cheap-baseline comparisons;
- safety review;
- external review;
- proof-ladder mapping;
- dataset cards;
- model cards;
- prior decision records.

## Safety impact

Does this decision affect:

- release status;
- candidate artifacts;
- model artifacts;
- external-facing docs;
- unsafe use risk;
- claim language?

## Scientific impact

Does this decision affect:

- scoring;
- ranking;
- benchmark status;
- calibration;
- candidate selection;
- proof-ladder level;
- interpretation of results?

## Decision

State the decision clearly.

## Why this decision

Explain why this decision is better than alternatives.

## What this does not prove

List boundaries and limitations.

## Revisit condition

What new evidence would trigger revisiting this decision?

## Follow-up tasks

- [ ] Task 1
- [ ] Task 2
```

## Decision classes

| Class | Meaning | Review |
|---|---|---|
| A | Routine docs or small bug fix | Maintainer review. |
| B | Infrastructure or compatibility change | Maintainer review and docs. |
| C | Scientific behavior change | Scientific/benchmark review. |
| D | Safety-sensitive or release-sensitive change | Safety review required. |

## Final rule

A decision record should make future disagreement easier, not harder.
