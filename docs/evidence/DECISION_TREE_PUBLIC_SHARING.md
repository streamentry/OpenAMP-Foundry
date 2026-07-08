# Decision Tree: Public Artifact Sharing

```mermaid
flowchart TD
  A[Share artifact publicly?] --> B{Contains sensitive data?}
  B -->|Yes| C[Redact or don't share]
  B -->|No| D{Is it a release artifact?}
  D -->|Yes| E[Follow PUBLICATION_PACK.md]
  D -->|No| F{Is it a benchmark result?}
  F -->|Yes| G[Include caveats]
  F -->|No| H[Share with standard disclaimer]
```
