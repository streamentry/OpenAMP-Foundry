---
name: Safety or release review
description: Request review for safety-sensitive, release-sensitive, or wet-lab-facing changes
title: "[safety-review] "
labels: ["safety", "needs-safety-review", "human-required", "do-not-automerge", "risk-high"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template for changes that may affect safety, release boundaries, candidate publication, model release, wet-lab-facing artifacts, public claims, or misuse risk.
  - type: textarea
    id: artifact
    attributes:
      label: Artifact or change under review
      description: What file, model, candidate panel, claim, or workflow needs review?
    validations:
      required: true
  - type: textarea
    id: intended_use
    attributes:
      label: Intended use
      description: What should this artifact be used for?
    validations:
      required: true
  - type: textarea
    id: disallowed_use
    attributes:
      label: Disallowed use
      description: What must this artifact not be used for?
    validations:
      required: true
  - type: textarea
    id: misuse
    attributes:
      label: Misuse scenarios
      description: How could this be misused or misread?
    validations:
      required: true
  - type: textarea
    id: mitigations
    attributes:
      label: Existing mitigations
      description: What policies, gates, docs, or defaults reduce risk?
      value: |
        - SAFETY.md
        - RESPONSIBLE_USE.md
        - MODEL_RELEASE_POLICY.md
        - docs/evidence/PROOF_LADDER.md
        - docs/review/EXTERNAL_REVIEW_PACKET.md
    validations:
      required: true
  - type: dropdown
    id: release_decision
    attributes:
      label: Proposed release decision
      options:
        - open release
        - staged release
        - restricted release
        - metadata-only release
        - delayed release
        - do not release
        - unknown / needs reviewer decision
    validations:
      required: true
  - type: textarea
    id: claim_level
    attributes:
      label: Claim level
      description: What proof-ladder level supports the intended claim?
      placeholder: "Example: Level 4 — computational evidence package only."
    validations:
      required: true
  - type: checkboxes
    id: boundaries
    attributes:
      label: Boundary checks
      options:
        - label: No wet-lab protocol or operational biological instruction is added.
          required: true
        - label: No harmful optimization objective is added.
          required: true
        - label: No unsupported efficacy, safety, clinical, or therapeutic claim is made.
          required: true
        - label: Candidate/model release status is explicit.
          required: true
        - label: Human safety review is required before merge or release.
          required: true
