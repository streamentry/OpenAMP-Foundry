---
name: Benchmark proposal or change
description: Propose, change, promote, or deprecate a benchmark
title: "[benchmark] "
labels: ["benchmark", "needs-baseline", "needs-benchmark", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template for benchmark proposals, benchmark changes, or benchmark interpretation updates. Read `docs/evidence/BENCHMARK_GOVERNANCE.md` before opening.
  - type: textarea
    id: question
    attributes:
      label: Benchmark question
      description: What question does this benchmark answer?
      placeholder: "Example: Does the ranker retain signal when charge density is matched between positives and negatives?"
    validations:
      required: true
  - type: textarea
    id: claim
    attributes:
      label: Claim gated or challenged
      description: What claim does this benchmark allow, block, or downgrade?
    validations:
      required: true
  - type: textarea
    id: dataset
    attributes:
      label: Dataset and license status
      description: What data is used, and what is its license/redistribution status?
    validations:
      required: true
  - type: textarea
    id: cheap_baselines
    attributes:
      label: Cheap baselines
      description: Which simple baselines must this benchmark compare against?
      value: |
        - random valid selection
        - charge or charge density
        - length
        - hydrophobicity
        - similarity to known AMPs
    validations:
      required: true
  - type: textarea
    id: shortcut_risks
    attributes:
      label: Shortcut and leakage risks
      description: How could this benchmark be fooled?
    validations:
      required: true
  - type: textarea
    id: metric
    attributes:
      label: Primary metric and threshold
      description: What metric will be reported? Is there a pre-registered threshold?
    validations:
      required: true
  - type: dropdown
    id: status
    attributes:
      label: Intended benchmark status
      options:
        - exploratory
        - informational
        - gate
        - kill benchmark
        - deprecation
    validations:
      required: true
  - type: textarea
    id: verification
    attributes:
      label: Verification plan
      description: Command, output artifact, tests, and docs that must change.
    validations:
      required: true
  - type: checkboxes
    id: review
    attributes:
      label: Review requirements
      options:
        - label: `docs/evidence/BENCHMARK_GOVERNANCE.md` considered.
          required: true
        - label: `docs/evidence/METRICS_CURRENT.md` will be updated if results change.
          required: true
        - label: Cheap-baseline comparison is included or explicitly deferred with reason.
          required: true
