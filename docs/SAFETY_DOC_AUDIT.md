# Safety Documentation Audit

## Purpose

This document records safety-relevant documentation risks and remediation decisions.

OpenAMP Foundry should be safe by architecture, not merely safe by disclaimer.

## Audit principle

Documentation can create capability.

A repo can avoid releasing model weights and still create risk if docs provide operational biological instructions, overclaim candidate status, or encourage unqualified testing.

Therefore, docs are part of the safety surface.

## Current audit decision

The repo’s external-facing lab documents have been refactored toward a safer boundary:

```text
old unsafe drift risk:
  computational handoff + operational assay detail

new standard:
  computational evidence package + qualified partner review boundary
```

OpenAMP should not be a wet-lab protocol repository.

OpenAMP should be a dry-lab evidence, review, and result-intake infrastructure project.

## Documents audited

| Document | Risk found | Remediation |
|---|---|---|
| `docs/review/WET_LAB_HANDOFF.md` | Mixed score interpretation with operational wet-lab guidance. | Refactored into safe expert-review handoff guide. |
| `docs/review/LAB_PARTNER_ONBOARDING.md` | Included synthesis and assay operational details. | Refactored into non-protocol partner onboarding and review-boundary doc. |
| `docs/review/ASSAY_PREREGISTRATION.md` | Included concrete assay parameters and operational procedure details. | Refactored into candidate-selection pilot pre-registration template. |
| `docs/review/EXPERT_REVIEW_PACK.md` | Included panel-specific candidate table and stronger review-to-testing language. | Refactored into reusable safe expert-review packet template. |
| `README.md` | Repo map did not fully reflect new governance and review docs. | Updated with governance, review, and safety-oriented entrypoints. |
| `.github/PULL_REQUEST_TEMPLATE.md` | Needed stronger proof-ladder and safety review checks. | Expanded PR template. |
| Issue templates | Missing structured safety/agent/benchmark triage. | Added agent-safe, benchmark-governance, and safety-review issue templates. |

## Safety boundary now enforced by docs

OpenAMP may provide:

- computational candidate evidence;
- manifests and certificates;
- benchmark summaries;
- baseline comparisons;
- novelty analysis;
- safety-risk flags;
- synthesis-feasibility flags at a non-operational level;
- external review packets;
- pre-registration of selection logic;
- structured result-intake schemas;
- calibration-gate outputs.

OpenAMP should not provide:

- wet-lab protocols;
- culturing instructions;
- organism-handling guidance;
- operational assay parameters;
- clinical recommendations;
- harmful optimization objectives;
- unscreened high-risk candidate dumps;
- claims of biological proof from computation.

## Why this improves positioning

The strongest open biotech infrastructure will not be the repo that shares the most operational detail.

It will be the repo that serious labs, institutions, safety reviewers, and agents can trust.

Trust requires clear boundaries:

- what is open;
- what is reviewed;
- what is restricted;
- what is not the repo’s job;
- what evidence is required before stronger claims.

This audit moves OpenAMP toward that standard.

## Ongoing audit triggers

Run a safety-doc audit when any of these occur:

- new wet-lab-facing doc;
- new candidate panel artifact;
- new model or generator artifact;
- new external partner workflow;
- public claim stronger than dry-lab nomination;
- benchmark result used in outreach;
- agent-generated docs touching biology;
- release of candidate identities or sequences.

## Safety-doc review checklist

Before merging external-facing docs, ask:

1. Does this include operational biological instructions?
2. Does this tell unqualified users how to test candidates?
3. Does this publish sensitive candidate details without review?
4. Does this imply biological activity without evidence?
5. Does this imply safety or clinical relevance?
6. Does this bypass qualified partner oversight?
7. Does this map claims to the proof ladder?
8. Does this preserve negative-result and failure-mode discipline?
9. Does this make misuse harder rather than easier?
10. Does this require human safety review?

## Final standard

OpenAMP should make qualified collaboration easier and unsafe self-directed biological experimentation harder.

That is the correct boundary for a serious open AI-bio infrastructure project.
