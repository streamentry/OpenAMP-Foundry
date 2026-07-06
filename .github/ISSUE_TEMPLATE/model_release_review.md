---
name: Model or artifact release review
description: Request review before releasing model weights, adapters, candidate panels, datasets, or sensitive artifacts
title: "[release-review] "
labels: ["needs-safety-review", "human-required", "do-not-automerge", "risk-high"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template for model, adapter, candidate-panel, dataset, or artifact release decisions. Read `MODEL_RELEASE_POLICY.md` first.
  - type: textarea
    id: artifact
    attributes:
      label: Artifact
      description: What artifact is being considered for release?
    validations:
      required: true
  - type: dropdown
    id: artifact_type
    attributes:
      label: Artifact type
      options:
        - model weights
        - scorer or predictor
        - generator
        - external adapter
        - candidate panel
        - dataset
        - result summary
        - benchmark artifact
        - review packet
        - other
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
    id: not_for
    attributes:
      label: Not for
      description: What must this artifact not be used for?
    validations:
      required: true
  - type: textarea
    id: evidence
    attributes:
      label: Evidence and limitations
      description: What evidence supports release, and what does it not prove?
    validations:
      required: true
  - type: textarea
    id: safety_risks
    attributes:
      label: Safety or misuse risks
      description: What could go wrong if this artifact is released?
    validations:
      required: true
  - type: dropdown
    id: proposed_release
    attributes:
      label: Proposed release decision
      options:
        - open release
        - staged release
        - metadata-only release
        - restricted release
        - internal only
        - do not release
        - needs reviewer decision
    validations:
      required: true
  - type: textarea
    id: references
    attributes:
      label: Required references
      value: |
        - MODEL_RELEASE_POLICY.md
        - SAFETY.md
        - RESPONSIBLE_USE.md
        - docs/trust/MODEL_CARD_TEMPLATE.md
        - docs/trust/RELEASE_CHECKLIST.md
    validations:
      required: true
  - type: checkboxes
    id: checks
    attributes:
      label: Required checks
      options:
        - label: Release status is explicit.
          required: true
        - label: Proof-ladder limit is explicit where claims are involved.
          required: true
        - label: Model/data card exists or is planned.
          required: true
        - label: Human safety review is required before release.
          required: true
