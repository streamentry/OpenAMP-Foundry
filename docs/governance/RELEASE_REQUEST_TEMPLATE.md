# Release Request Template

## Purpose

A release request is the formal artifact filed when a model, candidate, dataset, evidence packet, or schema is proposed for external release. File one whenever an artifact exits the internal pipeline and enters external distribution. The OpenAMP governance team reviews all requests before publication.

**Who reviews:** human_reviewer (GitHub handle) specified in the request. Review class determines scrutiny level.

---

## Template

Fill in every field. Fields marked REQUIRED must not be empty.

```yaml
release_id: ""            # Auto-assigned: REL-YYYY-NNN (REQUIRED)
release_type: ""          # candidate | model | dataset | evidence_packet | schema (REQUIRED)
artifact_id: ""           # Unique identifier for the artifact (REQUIRED)
artifact_version: ""      # Semantic version, e.g. 1.0.0 (REQUIRED)
requestor_name: ""        # Full name (REQUIRED)
requestor_institution: "" # Institution or organization (REQUIRED)
request_date: ""          # YYYY-MM-DD (REQUIRED)
evidence_level: 0         # Integer 1–6; dry-lab-only max is 4 (REQUIRED)
dry_lab_only: true        # Must be true — all releases are dry-lab only (REQUIRED)
safety_review_status: ""  # pending | approved | not_required (REQUIRED)
benchmark_summary: ""     # What baseline was beaten; must not be empty (REQUIRED)
known_limitations: ""     # Must not be empty (REQUIRED)
intended_use: ""          # research | internal | external_partner | public (REQUIRED)
data_license: ""          # e.g. CC-BY-4.0, Apache-2.0 (REQUIRED)
human_reviewer: ""        # GitHub handle of designated reviewer (REQUIRED)
review_class: ""          # A | B | C | D (REQUIRED)
approval_status: ""       # pending | approved | rejected | deferred (REQUIRED)
```

---

## Review Criteria

Reviewers check the following before approving:

1. **Completeness** — all required fields present and non-empty
2. **Release ID format** — starts with `REL-`
3. **Valid release type** — one of the five recognized types
4. **Evidence level** — within 1–6; dry-lab-only artifacts must not exceed 4
5. **Safety review** — public releases must not have `safety_review_status: pending`
6. **Benchmark summary** — non-trivial; describes what baseline was beaten
7. **Known limitations** — honestly stated; not a placeholder
8. **Data license** — explicitly named; no "TBD"
9. **Review class** — model releases typically require class C or D
10. **Dry-lab boundary** — `dry_lab_only` must be `true`; computational outputs are not biological proof

---

## Process

1. **File the request** — copy the template above, fill in all fields, open a GitHub issue titled `[Release Request] REL-YYYY-NNN — <artifact_id>`.
2. **Machine validation** — run `openamp-foundry release-request-check --request-json '{...}'` to pre-validate before human review.
3. **Human review** — the designated `human_reviewer` reviews within 5 business days.
4. **Decision** — reviewer sets `approval_status` to `approved`, `rejected`, or `deferred` with written rationale.
5. **Escalation** — if no decision within 10 business days, escalate to project maintainers via GitHub discussion.

**Expected timeline:** 5 business days for standard review; 10 business days for class D (model/safety-critical).

---

## Linked Policies

- [GOVERNANCE.md](../../GOVERNANCE.md)
- [SAFETY.md](../../SAFETY.md)
- [RESPONSIBLE_USE.md](../../RESPONSIBLE_USE.md)
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
- [DECISION_LOG.md](DECISION_LOG.md)
