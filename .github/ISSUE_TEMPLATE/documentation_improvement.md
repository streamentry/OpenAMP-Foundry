---
name: Documentation improvement
description: Propose a doc clarification, source-of-truth update, onboarding improvement, or consistency fix
title: "[docs] "
labels: ["docs", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template for documentation improvements that make the repo easier to understand, safer to use, or harder to misread.
  - type: textarea
    id: doc
    attributes:
      label: Document or section
      description: Which doc or section should change?
    validations:
      required: true
  - type: textarea
    id: problem
    attributes:
      label: Problem
      description: What is unclear, stale, duplicated, missing, or risky?
    validations:
      required: true
  - type: textarea
    id: improvement
    attributes:
      label: Proposed improvement
      description: What should the doc say or link to instead?
    validations:
      required: true
  - type: dropdown
    id: doc_class
    attributes:
      label: Documentation class
      options:
        - source of truth
        - onboarding
        - technical reference
        - safety or release
        - benchmark or metrics
        - external review
        - agent guidance
        - other
    validations:
      required: true
  - type: checkboxes
    id: checks
    attributes:
      label: Checks
      options:
        - label: This change does not strengthen scientific claims without evidence.
          required: true
        - label: This change does not remove safety caveats.
          required: true
        - label: `docs/PROJECT_INDEX.md` will be updated if this adds an important doc.
          required: true
