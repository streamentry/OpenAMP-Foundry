# Engineering Documentation

## Overview

Engineering docs describe architecture and reproducibility interfaces without
turning artifact presence into scientific validation.

## Key Components

- `ARCHITECTURE.md`: system, trust architecture, data flow, and gates.
- `RUN_MANIFEST_STANDARD.md`: provenance fields for reproducible runs.
- `SCHEMA_REGISTRY.md`: artifact prefixes and compatibility references.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Run["Pipeline run"] --> Manifest["Run manifest"] --> AARG["AARG- gate"]
  AARG --> Review["Reproducibility review"]
```
