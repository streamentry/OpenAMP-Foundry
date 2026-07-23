# Evidence Module

## Overview

Evidence records are dry-lab review artifacts. They must preserve limitations,
claim boundaries, reproducibility metadata, and explicit negative findings.

## Key Components

- `disconfirming_test_record.py`: one auditable attempt to disprove a claim.
- `phase_ac_disconfirming_gate.py`: aggregate gate for unresolved follow-up.
- `phase_z_accountability_gate.py`: aggregate gate for per-family benchmark
  and adapter accountability artifacts.
- `external_review_packet.py`: current V4 component-based review packet; its
  legacy Phase E bridge is migration-only.
- `domain_review_outcome.py`: records reviewer outcomes. Use its package-aware
  validator when the frozen PEP JSON is available; `pep_sha256` binds the
  outcome to that exact JSON but does not authenticate the reviewer or prove
  biology.

## Diagrams (Mermaid)

### Flowchart

```mermaid
flowchart TD
  DTR["DTR- record"] --> Validate["Validate record"]
  Validate --> Aggregate["Build ACDG- aggregate"]
  Aggregate --> Actions["Count claim-affecting actions"]
  Actions --> Verdict["Verified / partial / not established"]
```

### Component Diagram

```mermaid
flowchart LR
  Record["DisconfirmingTestRecord"] --> Gate["PhaseAcDisconfirmingGate"]
  Gate --> Review["Human claim review"]
  Gate -. "does not prove biology" .-> Boundary["Dry-lab boundary"]
```

### Sequence Diagram

```mermaid
sequenceDiagram
  participant Agent
  participant DTR
  participant ACDG
  participant Reviewer
  Agent->>DTR: record disconfirming test
  Agent->>ACDG: aggregate validated records
  ACDG-->>Reviewer: unresolved actions and verdict
  Reviewer->>ACDG: record explicit resolution
```

### Frozen review-package identity

```mermaid
flowchart LR
  PEP["Frozen PEP JSON"] --> Hash["stable_json_hash"]
  Outcome["DRO- outcome + pep_sha256"] --> Verify["Package-aware validator"]
  Hash --> Verify
  Verify -->|match| Bound["Identity bound"]
  Verify -->|missing or mismatch| Blocked["Fail closed"]
```
