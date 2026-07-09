# Maintainer Rotation and Bus-Factor Plan

## Purpose

OpenAMP Foundry's project durability depends on **bus-factor coverage** — the number of maintainers who must be lost before project operations stop. Every critical function must have at least two capable people.

This document:

- Lists current maintainers, their roles, and their backups.
- Defines what each role requires and is responsible for.
- Assesses bus-factor risk for every critical function (target: >=2).
- Describes the rotation schedule for reviewing assignments.
- Provides onboarding and offboarding checklists.

**Who should read this:** all current maintainers, contributors considering a maintainer role, and downstream consumers who need to know the project is durable.

**How to use:** Keep this document in the repo. Update it whenever a maintainer joins, leaves, or changes responsibilities. Review at least every 6 months.

## Current Maintainers

| GitHub handle | Role | Backup | Responsibilities |
|---|---|---|---|
| `lead-maintainer` | primary_maintainer | `backup-maintainer` | Release approvals, safety policy ownership, final PR approvals, phase planning, external liaison |
| `backup-maintainer` | secondary_maintainer | `lead-maintainer` | Day-to-day PR reviews, issue triage, CI maintenance, onboarding new contributors |
| `domain-advisor` | external_advisor | — | Domain-expertise consultation, D-class review participation, benchmark design input |

## Role Definitions

### primary_maintainer

- Owns the release process and safety policy.
- Provides final approval on PRs after at least one other review.
- Represents the project externally (partner discussions, governance).
- **Requires:** full commit access, safety-policy familiarity, release-checklist fluency, at least 6 months as secondary.

### secondary_maintainer

- Covers for primary during absences (up to full release authority on pre-planned leave).
- Owns day-to-day PR review queue and issue triage.
- Maintains CI, documentation, and onboarding processes.
- **Requires:** PR review experience, CI troubleshooting skills, governance-doc familiarity.

### external_advisor

- Provides domain expertise (antimicrobial peptide biology, assay design, computational chemistry).
- Participates in D-class (safety-significant) reviews.
- Does not hold commit access or release authority.
- **Requires:** relevant domain expertise; no commit access needed.

### contributor

- Submits PRs, participates in reviews, reports issues.
- Does not hold release keys or have offboarding responsibilities.
- **Requires:** familiarity with contribution guide and safety policy.

## Bus-Factor Assessment

| Function | Responsible | Backup | Bus factor |
|---|---|---|---|
| Release approval | `lead-maintainer` | `backup-maintainer` | 2 |
| Safety policy | `lead-maintainer` | `backup-maintainer` | 2 |
| PR review (final) | `lead-maintainer` | `backup-maintainer` | 2 |
| PR review (day-to-day) | `backup-maintainer` | `lead-maintainer` | 2 |
| Issue triage | `backup-maintainer` | `lead-maintainer` | 2 |
| CI maintenance | `backup-maintainer` | — | **1** |
| Domain expertise | `domain-advisor` | — | **1** |

**Target:** >= 2 for every critical function. CI maintenance and domain expertise currently have bus-factor 1 and should be improved when new maintainers join.

## Rotation Schedule

Roles are reviewed every **6 months** (March and September). The review process:

1. Primary sends a rotation-review thread to the maintainer mailing list.
2. Each maintainer confirms they want to continue in their current role or proposes a change.
3. Changes are documented in this file as a PR.
4. If the primary maintainer steps down, the secondary takes over and a new secondary is recruited.

Emergency handoffs (unexpected departure) follow the backup chain immediately. The offboarding checklist (below) must be completed within 14 days.

## Onboarding Checklist

A new maintainer must complete the following before taking a role:

- [ ] Read `docs/governance/GOVERNANCE.md`.
- [ ] Read `docs/governance/RELEASE_CHECKLIST.md`.
- [ ] Read `docs/governance/COI_DISCLOSURE_TEMPLATE.md`.
- [ ] Read `docs/governance/DECISION_LOG.md`.
- [ ] Read `docs/governance/RELEASE_REQUEST_TEMPLATE.md`.
- [ ] Read `docs/governance/MAINTAINER_ROTATION_PLAN.md` (this document).
- [ ] Read `SAFETY.md`.
- [ ] Read `RESPONSIBLE_USE.md`.
- [ ] Confirm they have read and agree to the project's safety and responsible-use policies.
- [ ] Add their GitHub handle, role, and backup to the Current Maintainers table in this file.
- [ ] Open a PR, get approval from at least one existing maintainer.

## Offboarding Checklist

A departing maintainer must:

- [ ] Notify the maintainer mailing list at least 14 days before departure (or as soon as practical for emergencies).
- [ ] Rotate any shared secrets, SSH keys, or service credentials they held.
- [ ] Document their current in-progress work (open PRs, issues assigned, CI state).
- [ ] Update the Current Maintainers table: set their status to "departing" and remove or reassign their responsibilities.
- [ ] Transfer any domain-specific knowledge to their backup (if one exists).
- [ ] Ensure this file is updated before they lose access.

## Scope

This document is a governance artifact, not a legal determination. Maintainer roles are project responsibilities, not employment relationships. Bus-factor assessment is a project-durability estimate, not a security guarantee.

## Linked Policies

- `docs/governance/GOVERNANCE.md`
- `docs/governance/RELEASE_CHECKLIST.md`
- `docs/governance/COI_DISCLOSURE_TEMPLATE.md`
- `docs/governance/DECISION_LOG.md`
- `docs/governance/RELEASE_REQUEST_TEMPLATE.md`
- `SAFETY.md`
- `RESPONSIBLE_USE.md`
