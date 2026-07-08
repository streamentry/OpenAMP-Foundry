# Documentation Governance Charter

## Purpose

This charter defines how documentation is governed in the OpenAMP Foundry project.

## Principles

1. **Truthfulness first** — documentation must not overclaim.
2. **Single source of truth** — `docs/evidence/METRICS_CURRENT.md` is authoritative for metrics.
3. **Freshness** — documents should be reviewed on a regular cadence.
4. **Accessibility** — documents should be findable from PROJECT_INDEX.md.
5. **Accountability** — every document has an owner (maintainer or designated reviewer).

## Document Types

| Type | Description | Review Cadence |
|------|-------------|----------------|
| Policy | Rules and governance | Every 6 months |
| Guide | How-to instructions | Every 3 months |
| Reference | Factual documentation | Every 6 months |
| Concept card | Short explanations | Annually |
| Runbook | Step-by-step procedures | Every 3 months |

## Change Process

- **Minor changes** (typos, formatting): Direct commit to main or PR with `minor` label.
- **Major changes** (new policy, restructuring): Standard PR with full review.
- **Urgent fixes** (safety, accuracy): Immediate fix + 24h review.

## Roles

See `docs/evidence/DOCS_ROLE_DEFINITIONS.md` for role descriptions.

## Related Documents

- `docs/evidence/DOCS_MINOR_EDIT_POLICY.md`
- `docs/evidence/DOCS_REVIEW_CADENCE_POLICY.md`
- `docs/evidence/DOCS_RETIREMENT_POLICY.md`
- `docs/evidence/DOCS_ESCALATION_POLICY.md`
- `docs/evidence/DOCS_EXCEPTION_POLICY.md`
