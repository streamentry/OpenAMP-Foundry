# Novelty Scripts

## Overview

This folder is the canonical home for novelty-database refresh, novelty audit,
and patent-risk search entrypoints.

## Key Components

- `download_novelty_dbs.py`
- `run_novelty_audit.py`
- `run_expanded_novelty_audit.py`
- `run_patent_blastp.py`

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  DBs["Novelty databases"] --> Refresh["download_novelty_dbs.py"]
  Refresh --> Audit["run_novelty_audit.py"]
  Refresh --> Expanded["run_expanded_novelty_audit.py"]
  Expanded --> Patent["run_patent_blastp.py"]
```

- Component Diagram

```mermaid
flowchart LR
  NoveltyScripts["scripts/novelty"] --> Data["data/novelty_db"]
  NoveltyScripts --> Outputs["outputs/*novelty*"]
  NoveltyScripts --> Docs["docs/NOVELTY_AUDIT_GUIDE.md"]
  Tests["tests/novelty"] --> NoveltyScripts
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Maintainer
  participant Refresh
  participant Audit
  participant Patent
  Maintainer->>Refresh: refresh novelty DBs
  Refresh->>Audit: provide reference corpus
  Audit->>Patent: identify candidates needing IP review
  Patent-->>Maintainer: novelty and patent-risk evidence
```
