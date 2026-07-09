# Governance Decision Log

## Purpose

This document records all significant governance decisions made in the OpenAMP
Foundry project. It exists to make decisions discoverable, auditable, and
reviewable by both humans and automated tooling.

**Maintainer:** Project maintainers (via PR review).

**How to add entries:**

1. File a GitHub issue describing the proposed governance decision.
2. Obtain review from at least one project maintainer.
3. Add a new row to the decision index with a unique GOV-NNN ID.
4. Update `src/openamp_foundry/governance/decision_log.py` with the new
   `GovernanceDecision` entry.
5. Run `make decision-log` to validate the entry.

## Decision Index

| ID | Date | Scope | Decision | Status | Rationale | Review class |
|----|------|-------|----------|--------|-----------|-------------|
| GOV-001 | 2026-07-01 | safety | All artifacts must have `dry_lab_only=True`; computational outputs are not biological proof. | active | Prevents overclaiming computational results as wet-lab evidence. | D |
| GOV-002 | 2026-07-01 | evidence | Dry-lab-only artifacts are capped at evidence level 4; levels 5-6 require wet-lab evidence. | active | Maintains honest proof-ladder levels that cannot be inflated by simulation alone. | D |
| GOV-003 | 2026-07-04 | benchmark | Any module claiming ranking authority must beat a cheap baseline benchmark first. | active | Prevents simulation theater — modules that don't beat trivial baselines must not rank candidates. | B |
| GOV-004 | 2026-07-09 | contribution | All `wet_lab_validation` contributions require `human_review_required=True`. | active | Experimental data entering the pipeline must be reviewed by a human before use. | D |
| GOV-005 | 2026-07-09 | release | All external releases must pass the release gate validator before publication. | active | Prevents skipping required checks during release; gates are documented and enforced. | B |
| GOV-006 | 2026-07-09 | docs | Documentation files must remain under 200KB each. | active | Keeps docs readable and prevents runaway history accumulation. | B |
| GOV-007 | 2026-07-01 | evidence | Proof-ladder levels above 4 require wet-lab evidence and human review class D. | active | Calibrates claim strength to actual experimental evidence. | D |
| GOV-008 | 2026-07-04 | adapter | Adapter default mode is off or info; gated mode requires benchmark comparison. | active | Prevents external adapters from silently influencing rankings without evidence. | B |

## How to Add a New Entry

1. **Open an issue** on GitHub describing the proposed decision, its scope,
   rationale, and intended review class.
2. **Receive review** from at least one project maintainer. Review class D
   decisions require documented human review.
3. **Assign a new GOV-NNN ID** (increment the highest existing number).
4. **Add the entry** to the table above and to the
   `GOVERNANCE_DECISIONS` list in
   `src/openamp_foundry/governance/decision_log.py`.
5. **Validate** with `make decision-log` (runs `openamp-foundry decision-log --validate`).
6. **Submit a PR** referencing the original issue.

## Linked Policies

- `docs/governance/GOVERNANCE.md` — Governance overview and role definitions.
- `SAFETY.md` — Safety policy and scope restrictions.
- `RESPONSIBLE_USE.md` — Allowed and disallowed uses.
- `docs/governance/RELEASE_CHECKLIST.md` — Release gate checklist (J1).

---

*This decision log is a dry-lab governance artifact. It documents policy
decisions, not biological findings. All entries carry `dry_lab_only: True`.*
