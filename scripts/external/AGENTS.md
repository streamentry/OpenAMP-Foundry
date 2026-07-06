# External Scripts

## Overview

This folder is the canonical home for external predictor submission, result
normalization, cross-tool consensus, and sponsor-facing handoff assembly.

## Key Components

- `create_predictor_results.py`
- `prepare_external_submission.py`
- `convert_ampactipred.py`
- `convert_macrel_web.py`
- `external_consensus.py`
- `build_sponsor_packet.py`

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  Panel["Pilot or expert panel"] --> Submit["prepare_external_submission.py"]
  Submit --> Tools["External predictor tools"]
  Tools --> Normalize["convert_* scripts"]
  Normalize --> Consensus["external_consensus.py"]
  Consensus --> Packet["build_sponsor_packet.py"]
```

- Component Diagram

```mermaid
flowchart LR
  ExternalScripts["scripts/external"] --> Validation["outputs/external_validation"]
  ExternalScripts --> Submission["outputs/external_submission"]
  ExternalScripts --> Handoff["handoff/sponsor_packet"]
  Tests["tests/external"] --> ExternalScripts
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Maintainer
  participant Submit
  participant Convert
  participant Consensus
  participant Packet
  Maintainer->>Submit: emit FASTAs and summary
  Submit->>Convert: collect exported tool outputs
  Convert->>Consensus: normalized per-tool calls
  Consensus->>Packet: recommended shortlist and evidence
```
