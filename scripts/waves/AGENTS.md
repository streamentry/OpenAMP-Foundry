# Wave Scripts

## Overview

This folder is the canonical home for wave-program execution scripts:
Wave 0.5/0.5b generation, filtering, novelty audit, external fill, evidence
packaging, and final panel selection.

## Key Components

- `generate_wave0_5_candidates.py`
- `filter_wave0_5_candidates.py`
- `run_wave0_5_novelty_audit*.py`
- `fill_wave0_5_external_results.py`
- `select_wave1_panel.py`
- `generate_wave0_5_evidence_certs.py`
- `generate_wave0_5b_candidates.py`
- `filter_wave0_5b_candidates.py`

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  Generate["Generate candidates"] --> Filter["Internal filter"]
  Filter --> Novelty["Novelty audit"]
  Novelty --> External["External predictor fill"]
  External --> Panel["Final panel selection"]
  Panel --> Evidence["Evidence certificate generation"]
```

- Component Diagram

```mermaid
flowchart LR
  WaveScripts["scripts/waves"] --> Outputs["outputs/wave0_5_*"]
  WaveScripts --> Docs["wave docs and plans"]
  WaveScripts --> Src["src/openamp_foundry/*"]
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Maintainer
  participant Generate
  participant Audit
  participant Select
  participant Evidence
  Maintainer->>Generate: create raw wave candidates
  Generate->>Audit: send shortlist to novelty audit
  Audit->>Select: provide novelty-classified pool
  Select->>Evidence: finalize candidates for certificates
```
