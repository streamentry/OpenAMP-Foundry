---
name: Bug report
description: Report a reproducible software, documentation, schema, or command issue
title: "[bug] "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template for normal software or documentation bugs. Keep examples minimal and safe. Use private reporting for sensitive material.
  - type: textarea
    id: summary
    attributes:
      label: Summary
      description: What went wrong?
    validations:
      required: true
  - type: textarea
    id: reproduce
    attributes:
      label: Steps to reproduce
      description: Include commands, toy inputs, or safe minimal examples.
      placeholder: |
        1. ...
        2. ...
        3. ...
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
    validations:
      required: true
  - type: textarea
    id: observed
    attributes:
      label: Observed behavior
    validations:
      required: true
  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: Python version, OS, install method, package version, or commit.
    validations:
      required: false
  - type: textarea
    id: artifacts
    attributes:
      label: Safe artifacts or logs
      description: Paste safe logs only. Do not include credentials, restricted data, or unreleased artifacts.
    validations:
      required: false
  - type: checkboxes
    id: checks
    attributes:
      label: Checks
      options:
        - label: This report does not include private credentials or tokens.
          required: true
        - label: This report does not include restricted data or unreleased artifacts.
          required: true
        - label: This report belongs in a public issue rather than private reporting.
          required: true
