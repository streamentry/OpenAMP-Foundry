# Lab Scripts

## Overview

This folder is the canonical home for lab handoff utilities: building partner
packs, validating returned data, and checking pre-registered batch criteria.

## Key Components

- `build_lab_batch_pack.py`: package candidate artifacts for qualified labs.
- `validate_lab_data_return.py`: validate returned JSON results.
- `check_wave1_pass_fail.py`: evaluate batch results against frozen criteria.

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  Ranked["Ranked panel + evidence"] --> Pack["build_lab_batch_pack.py"]
  Pack --> Lab["Qualified lab partner"]
  Lab --> Return["Returned JSON results"]
  Return --> Validate["validate_lab_data_return.py"]
  Validate --> Verdict["check_wave1_pass_fail.py"]
```

- Component Diagram

```mermaid
flowchart LR
  LabScripts["scripts/lab"] --> Docs["docs/WET_LAB_HANDOFF.md"]
  LabScripts --> Schemas["schemas/lab_result.schema.json"]
  LabScripts --> Outputs["outputs/lab_batch_pack.zip"]
  Tests["tests/lab"] --> LabScripts
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Maintainer
  participant Pack as build_lab_batch_pack
  participant Lab
  participant Validate as validate_lab_data_return
  participant Check as check_wave1_pass_fail
  Maintainer->>Pack: build pack
  Pack->>Lab: deliver review packet
  Lab->>Validate: return results
  Validate->>Check: validated result set
  Check-->>Maintainer: pass/fail verdict
```
