# Conflict-of-Interest Disclosure Template

## Purpose

A conflict-of-interest (COI) disclosure is filed when a contributor, reviewer, maintainer, or external advisor has a potential conflict with an artifact, decision, or review they are involved with. Filing a disclosure enables transparent governance and builds institutional trust.

**File a disclosure when you have:**
- A financial interest in an artifact or organization related to the work
- An institutional relationship (current or former employer, funder) with a stakeholder
- A competitive relationship with parties being evaluated
- A personal relationship that could influence objectivity

**Who reviews:** the designated `reviewer` (GitHub handle) noted in the disclosure.

---

## Template

Fill in every field. Fields marked REQUIRED must not be empty.

```yaml
disclosure_id: ""         # e.g. COI-2026-001 (REQUIRED)
disclosure_type: ""       # reviewer | contributor | maintainer | external_advisor (REQUIRED)
subject: ""               # GitHub handle of person filing disclosure (REQUIRED)
related_artifact: ""      # artifact ID or PR number (REQUIRED)
relationship_type: ""     # financial | institutional | competitive | personal | none (REQUIRED)
description: ""           # Required when relationship_type != "none"; leave empty only if "none"
disclosure_date: ""       # YYYY-MM-DD (REQUIRED)
recusal_required: false   # true | false (REQUIRED)
reviewer: ""              # GitHub handle of designated reviewer (REQUIRED)
review_status: ""         # pending | acknowledged | resolved (REQUIRED)
```

---

## When to Disclose

| Relationship type | Examples | Typical action |
|---|---|---|
| financial | equity, grants, consulting fees from a related org | Disclose; recusal often required |
| institutional | current/former employer, department, funder | Disclose; recusal case-by-case |
| competitive | org whose product competes with the artifact | Disclose; recusal recommended |
| personal | close family, romantic partner, close friend | Disclose; recusal case-by-case |
| none | no conflict | File with description="" to document clean slate |

---

## Process

1. **File the disclosure** — copy the template above, fill in all fields, open a GitHub issue titled `[COI Disclosure] COI-YYYY-NNN — <subject>`.
2. **Machine validation** — run `openamp-foundry coi-check --disclosure-json '{...}'` to pre-validate.
3. **Human review** — the designated `reviewer` acknowledges within 3 business days.
4. **Decision** — reviewer sets `review_status` to `acknowledged` or `resolved` with written rationale on recusal.
5. **Escalation** — if no acknowledgment within 5 business days, escalate to project maintainers via GitHub discussion.

---

## Linked Policies

- [GOVERNANCE.md](../../GOVERNANCE.md)
- [RESPONSIBLE_USE.md](../../RESPONSIBLE_USE.md)
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
- [DECISION_LOG.md](DECISION_LOG.md)
