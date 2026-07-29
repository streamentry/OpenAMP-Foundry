# Repository Checks

## Overview

This package contains deterministic repository-integrity checks. These checks
inspect source, documentation, and generated metadata; they do not validate
biological activity, safety, or release readiness.

## Key Components

- `stale_doc_detector.py` finds backtick-quoted, repo-relative file references
  in documentation and reports references whose targets no longer exist.
- Check formatters keep summary metrics distinct from detail-section headings
  so clean and failing output remain human- and machine-readable.

## Diagrams

### Flowchart

```mermaid
flowchart LR
  Docs["Documentation"] --> Scan["Integrity check"]
  Scan --> Report["Summary + details"]
  Report --> Review["Agent or human review"]
```

### Component Diagram

```mermaid
flowchart TB
  Detector["stale_doc_detector"] --> Paths["Repository paths"]
  Detector --> Findings["StaleDocReport"]
  Findings --> Formatter["Human-readable formatter"]
```

### Sequence Diagram

```mermaid
sequenceDiagram
  participant Caller
  participant Detector
  participant Filesystem
  Caller->>Detector: scan docs
  Detector->>Filesystem: resolve referenced paths
  Filesystem-->>Detector: exists / missing
  Detector-->>Caller: report
```
