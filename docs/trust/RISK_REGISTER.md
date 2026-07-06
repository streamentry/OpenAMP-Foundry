# Risk Register

## Purpose

This document records major risks that could prevent OpenAMP Foundry from becoming trustworthy open infrastructure.

A serious project should name its risks before critics do.

## Prime rule

**A risk that is named can be governed. A risk that is hidden becomes culture.**

## Risk categories

| Category | Meaning |
|---|---|
| Safety | Misuse, unsafe release, or unsafe scope. |
| Scientific | False claims, weak benchmarks, leakage, overfitting. |
| Operational | Maintainer overload, brittle workflows, poor onboarding. |
| Ecosystem | Low adoption, unclear interfaces, weak interoperability. |
| Governance | Poor decision records, unclear review authority. |
| Agentic | Agent scope creep, overclaiming, unsafe autonomous edits. |

## Current top risks

### R1 — Claim inflation

Risk: dry-lab ranking is described as biological discovery.

Mitigation:

- proof ladder;
- claim review checklist;
- PR template claim section;
- reviewer onboarding;
- publication policy.

### R2 — Benchmark theater

Risk: benchmarks look impressive but mostly measure charge, length, source artifacts, or leakage.

Mitigation:

- benchmark governance;
- cheap-baseline comparisons;
- charge-matched and family-stratified checks;
- metrics source-of-truth;
- benchmark cards.

### R3 — Unsafe release

Risk: candidate panels, model artifacts, or external-facing summaries are released before safety review.

Mitigation:

- model release policy;
- safety policy;
- release checklist;
- safety review issue template;
- CODEOWNERS review intent.

### R4 — Agent scope creep

Risk: agents make broad changes, strengthen claims, or touch safety-sensitive areas without review.

Mitigation:

- agent operating contract;
- human-agent collaboration model;
- issue labels;
- agent-safe issue template;
- stop conditions.

### R5 — Documentation drift

Risk: docs disagree with code, metrics, or safety policy.

Mitigation:

- docs maintenance standard;
- project index;
- source-of-truth docs;
- CI/doc checks roadmap;
- release checklist.

### R6 — Artifact instability

Risk: external users cannot rely on schemas, manifests, or certificates.

Mitigation:

- artifact versioning;
- schema registry;
- run manifest standard;
- compatibility review.

### R7 — Data confusion

Risk: labels, licenses, negative sets, or preprocessing are unclear.

Mitigation:

- data governance;
- dataset cards;
- data contribution issue template;
- benchmark governance.

### R8 — External review bottleneck

Risk: the project has strong internal discipline but cannot get qualified external critique.

Mitigation:

- external review packet;
- reviewer onboarding;
- lab partner onboarding;
- adoption strategy;
- adoption metrics.

### R9 — Simulation overtrust

Risk: virtual-assay proxy outputs are treated as validated substitutes.

Mitigation:

- virtual assay scope;
- simulation benchmark;
- adapter guide;
- benchmark gates;
- proof ladder.

### R10 — Maintainer bus factor

Risk: only one person understands the project’s rationale.

Mitigation:

- governance;
- decision records;
- maintainer guide;
- project index;
- next 100 PR map.

## Risk review cadence

Review this register:

- before major releases;
- after safety-sensitive changes;
- after benchmark surprises;
- after external review;
- after agent-generated broad changes;
- quarterly if the project is active.

## Risk entry template

```md
### R<n> — <risk name>

Risk:

Why it matters:

Likelihood: low | medium | high

Impact: low | medium | high

Mitigation:

Owner:

Review date:

Revisit condition:
```

## Final standard

OpenAMP should be able to say: here are the ways we might be wrong, and here is how the repo is designed to find out.
