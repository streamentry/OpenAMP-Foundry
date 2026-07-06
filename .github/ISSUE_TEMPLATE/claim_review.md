---
name: Claim review
description: Review public wording, docs, release notes, or candidate/benchmark claims against the proof ladder
title: "[claim-review] "
labels: ["needs-proof-ladder-check", "docs", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template when wording may exceed evidence: README updates, release notes, benchmark summaries, candidate summaries, external review packets, announcements, or agent-generated text.
  - type: textarea
    id: claim
    attributes:
      label: Claim or wording under review
      description: Paste the exact wording or summarize the proposed claim.
    validations:
      required: true
  - type: textarea
    id: evidence
    attributes:
      label: Supporting evidence
      description: What evidence supports this claim?
    validations:
      required: true
  - type: dropdown
    id: proof_level
    attributes:
      label: Proof-ladder level
      options:
        - Level 0 — valid input
        - Level 1 — reproducible dry-lab features
        - Level 2 — baseline-triaged candidate
        - Level 3 — leakage-aware benchmark support
        - Level 4 — multi-signal candidate evidence
        - Level 5 — expert-reviewed assay proposal
        - Level 6 — initial qualified assay result
        - Level 7 — safety-adjusted follow-up signal
        - Level 8 — independent replication
        - Level 9 — reusable discovery loop
        - Level 10 — translational or clinical relevance
        - unknown / needs review
    validations:
      required: true
  - type: textarea
    id: unsupported
    attributes:
      label: What this does not prove
      description: List claims that must not be implied.
    validations:
      required: true
  - type: textarea
    id: safer_wording
    attributes:
      label: Safer wording
      description: Propose a weaker, evidence-aligned version.
    validations:
      required: true
  - type: checkboxes
    id: checks
    attributes:
      label: Checks
      options:
        - label: `docs/evidence/PROOF_LADDER.md` reviewed.
          required: true
        - label: `docs/evidence/CLAIM_REVIEW_CHECKLIST.md` reviewed.
          required: true
        - label: Dry-lab outputs are not described as biological proof.
          required: true
        - label: Safety, clinical, or therapeutic claims are not made without sufficient evidence.
          required: true
