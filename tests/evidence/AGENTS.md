# Evidence Tests

## Overview

Evidence tests protect schema invariants, negative findings, and claim
boundaries. Focused gate tests must cover empty, partial, resolved, and
malformed records.

## Key Components

- `test_phase_ac_disconfirming_gate.py`: ACDG- aggregate behavior.
- `test_disconfirming_test_record.py`: DTR- record invariants.
- `test_external_review_packet.py`: current V4 ERP contract.
- `test_domain_review_outcome.py`: legacy DRO validation plus fail-closed
  frozen-package hash binding when a PEP JSON is supplied.

## Diagrams (Mermaid)

### Flowchart

```mermaid
flowchart TD
  Fixture["Controlled fixture"] --> Builder["Artifact builder"]
  Builder --> Validator["Schema validator"]
  Validator --> Assertion["Expected gate or rejection"]
```

### Component Diagram

```mermaid
flowchart LR
  DTRTests["DTR tests"] --> DTRCode["DTR implementation"]
  ACDGTests["ACDG tests"] --> ACDGCode["ACDG implementation"]
  ERPTests["ERP tests"] --> ERPCode["ERP implementation"]
```

### Sequence Diagram

```mermaid
sequenceDiagram
  participant Pytest
  participant Fixture
  participant Artifact
  Pytest->>Fixture: construct controlled input
  Fixture->>Artifact: call builder
  Artifact-->>Pytest: validate or raise
  Pytest->>Pytest: assert claim boundary and counts
```
