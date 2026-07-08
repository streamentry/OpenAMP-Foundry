# Human-Agent Collaboration Model

## Purpose

This document defines how humans and AI agents should collaborate on OpenAMP Foundry.

The goal is not maximum agent autonomy.

The goal is safe, reviewable, compounding work.

## Collaboration thesis

AI agents are excellent at repetitive infrastructure work when the repo provides strong rails.

Humans are responsible for judgment: safety, scientific interpretation, release decisions, partner readiness, and claims.

OpenAMP should combine both:

```text
agents produce reviewable artifacts
humans make accountable decisions
```

## Division of labor

| Work | Agent role | Human role |
|---|---|---|
| Tests | Add, run, repair. | Review coverage and intent. |
| Docs | Draft and maintain. | Approve scope and claims. |
| Schemas | Draft, validate, add examples. | Approve compatibility and meaning. |
| Benchmarks | Scaffold and run. | Approve interpretation and thresholds. |
| Candidate artifacts | Package and validate. | Approve release and external use. |
| Model cards | Draft metadata. | Approve claims, limits, release status. |
| Data cards | Draft structure. | Verify license, labels, release status. |
| Safety docs | Suggest improvements. | Approve final policy. |
| External packets | Assemble drafts. | Approve readiness and release. |
| Calibration | Generate reports. | Decide whether to update behavior. |

## Maintainer prompts for assigning agent-safe tasks

When assigning a task to an agent, include these elements:

- **Task:** one-line description
- **Issue:** link to GitHub issue
- **Scope:** what files/directories to touch
- **Safety check:** what NOT to change — policy, release, benchmarks, thresholds
- **Evidence:** what test or command proves it works
- **Stop conditions:** what triggers asking for human review
- **Expected complexity:** prefer small

Example:

```
Task: Add doc-link check for new docs
Issue: https://github.com/Open-Problem-Lab/OpenAMP-Foundry/issues/732
Scope: docs/evidence/ directory only
Safety check: Do not change AGENTS.md, SAFETY.md, or any policy doc
Evidence: python scripts/check_doc_links.py shows 0 broken
Stop conditions: If task requires changing pipeline code, stop and ask
Expected complexity: small
```

## Agent-safe work

Agent-safe work is narrow, low-risk, and verifiable.

Examples:

- doc link repair;
- schema examples;
- tests for existing behavior;
- deterministic report improvements;
- toy-data examples;
- issue template improvements;
- benchmark-card scaffolding;
- claim-check tooling;
- data/model card templates;
- source-of-truth index updates.

## Human-required work

Human review is required for:

- safety policy changes;
- release policy changes;
- external partner-facing docs;
- candidate release;
- model release;
- non-toy data release;
- benchmark threshold changes;
- calibration policy changes;
- public claim upgrades;
- result interpretation;
- institutional collaborations.

## Collaboration modes

### Mode 1 — Agent drafts, human reviews

Best for docs, templates, schemas, and issue workflows.

Agent produces a draft and marks review needs.

Human checks meaning, safety, and claim level.

### Mode 2 — Agent implements, human verifies

Best for tests, validators, CLI ergonomics, and reports.

Agent implements narrow code changes.

Human verifies expected behavior and scope.

### Mode 3 — Human specifies, agent executes

Best for repetitive or multi-file maintenance.

Human states exact files, allowed scope, and stop conditions.

Agent executes without broadening scope.

### Mode 4 — Agent audits, human decides

Best for claim drift, doc drift, stale links, and benchmark caveats.

Agent finds issues and proposes fixes.

Human decides whether the interpretation is correct.

## Review packet for agent work

Every nontrivial agent contribution should answer:

- What changed?
- Why was this needed?
- What evidence verifies it?
- What safety boundary applies?
- What proof-ladder level is involved?
- What human review is required?
- What remains unproven?

## Agent failure modes

### Scope creep

Agent starts with a small task and rewrites a broad area.

Mitigation: stop conditions and file list.

### Claim inflation

Agent makes wording sound more impressive than evidence.

Mitigation: proof ladder and claim checklist.

### Safety dilution

Agent removes caveats to improve readability.

Mitigation: safety review for sensitive docs.

### Benchmark theater

Agent adds metrics that do not test the claim.

Mitigation: benchmark governance and cheap baselines.

### Hidden incompatibility

Agent changes artifact shape without versioning.

Mitigation: artifact versioning policy.

## Human failure modes

### Vague delegation

Human asks for “make it better” without scope.

Mitigation: define target, files, evidence, stop conditions.

### Hype pressure

Human rewards impressive wording over accurate wording.

Mitigation: claim review checklist.

### Review fatigue

Human rubber-stamps broad agent changes.

Mitigation: change classes and required review labels.

### Oral-tradition decisions

Human decisions happen outside repo history.

Mitigation: decision records.

## Ideal issue for agents

A good agent issue includes:

- problem statement;
- allowed files;
- forbidden files;
- expected artifact;
- commands or checks to run;
- source-of-truth docs;
- safety impact;
- proof level;
- stop condition.

Use `.github/ISSUE_TEMPLATE/agent_safe_task.md`.

## Ideal PR from agents

A good agent PR is:

- narrow;
- easy to review;
- testable;
- explicit about limitations;
- explicit about safety impact;
- linked to relevant docs;
- honest about what it does not prove.

## Final standard

OpenAMP should be one of the best repositories in the world for safe human-agent scientific infrastructure work.

Not because agents are trusted blindly.

Because the repo makes blind trust unnecessary.
