---
name: Agent-safe task
description: A narrow, low-risk task suitable for AI agents or new contributors
title: "[agent-safe] "
labels: ["agent-safe", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template for narrow tasks that can be completed without changing safety policy, wet-lab-facing artifacts, candidate release, benchmark thresholds, calibration policy, or biological claims.
  - type: textarea
    id: bottleneck
    attributes:
      label: Bottleneck
      description: What specific problem should be fixed?
      placeholder: "Example: CLI error message does not tell user which required CSV column is missing."
    validations:
      required: true
  - type: textarea
    id: expected_artifact
    attributes:
      label: Expected artifact or behavior
      description: What should exist or change after this issue is complete?
    validations:
      required: true
  - type: textarea
    id: allowed_scope
    attributes:
      label: Allowed scope
      description: What files or behaviors may be changed?
    validations:
      required: true
  - type: textarea
    id: forbidden_scope
    attributes:
      label: Forbidden scope
      description: What must not be changed?
      value: |
        - No wet-lab protocol or operational biological detail.
        - No candidate release.
        - No safety policy change.
        - No benchmark threshold change.
        - No claim strengthening.
    validations:
      required: true
  - type: textarea
    id: verification
    attributes:
      label: Verification
      description: Which command, test, schema validation, or doc check should verify the work?
      placeholder: "Example: pytest tests/test_cli_errors.py -v"
    validations:
      required: true
  - type: textarea
    id: docs
    attributes:
      label: Relevant docs
      description: Which docs should the contributor or agent read first?
      value: |
        - docs/getting-started/AGENT_ONBOARDING.md
        - docs/operations/HIGH_LEVERAGE_TASKS.md
        - SAFETY.md
    validations:
      required: true
  - type: checkboxes
    id: safety
    attributes:
      label: Safety check
      options:
        - label: This task does not add biological misuse capability.
          required: true
        - label: This task does not add wet-lab instructions.
          required: true
        - label: This task does not publish candidate sequences or model weights.
          required: true
        - label: This task does not strengthen scientific claims.
          required: true
