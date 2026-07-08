# Docs Source-of-Truth Tags

Standard tags to mark the authoritative source for a piece of information.

## Tags
| Tag | Meaning | Example |
|-----|---------|---------|
| `<!-- source-of-truth: METRICS_CURRENT.md -->` | Metrics authority | Benchmark values |
| `<!-- source-of-truth: EVIDENCE_CERTIFICATE.md -->` | Evidence authority | Certificate schema |
| `<!-- source-of-truth: AGENTS.md -->` | Agent rules authority | Agent operating principles |

## Rules
- Every document that contains authoritative information should be tagged.
- Tags are HTML comments in markdown files.
- Tags should reference the single source of truth document.
- If a tag is missing, add it when you find the source of truth.
