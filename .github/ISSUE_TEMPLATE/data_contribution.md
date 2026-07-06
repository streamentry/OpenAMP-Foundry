---
name: Data contribution or dataset review
description: Propose a dataset, reference set, benchmark data source, or result-summary contribution
title: "[data] "
labels: ["data", "needs-doc-update", "needs-safety-review", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template for non-toy data contributions or dataset review. Read `DATA_LICENSE_NOTICE.md` and `docs/DATA_GOVERNANCE.md` first.
  - type: textarea
    id: dataset
    attributes:
      label: Dataset or data artifact
      description: What data source or artifact is being proposed?
    validations:
      required: true
  - type: dropdown
    id: data_class
    attributes:
      label: Data class
      options:
        - toy/demo data
        - public redistributable data
        - public reference-only data
        - restricted data
        - generated candidate data
        - result-summary data
        - unknown
    validations:
      required: true
  - type: textarea
    id: license
    attributes:
      label: License and redistribution status
      description: What are the license, terms, citation, and redistribution limits?
    validations:
      required: true
  - type: textarea
    id: intended_use
    attributes:
      label: Intended use
      description: Reference, benchmark, training, validation, demo, result-intake, or other?
    validations:
      required: true
  - type: textarea
    id: labels
    attributes:
      label: Label definitions and known biases
      description: What do labels mean, and what biases or shortcut risks exist?
    validations:
      required: true
  - type: textarea
    id: preprocessing
    attributes:
      label: Preprocessing and provenance
      description: How will the data be fetched, transformed, deduplicated, and validated?
    validations:
      required: true
  - type: textarea
    id: release_status
    attributes:
      label: Safety-release status
      description: Should this data be open, metadata-only, restricted, internal, or not released?
    validations:
      required: true
  - type: checkboxes
    id: checks
    attributes:
      label: Required checks
      options:
        - label: Dataset card will be added for non-toy data.
          required: true
        - label: Raw third-party data will not be committed unless redistribution is clearly allowed.
          required: true
        - label: Safety review will occur if the data is sensitive, candidate-derived, or result-derived.
          required: true
        - label: Benchmark governance will be followed if used for a benchmark.
          required: true
