# Documentation Health Metric Definitions

This document defines the core metrics used to assess documentation health.

## Metric Definitions

| Metric | Definition | Collection Method | Target |
|--------|------------|-------------------|--------|
| Link health | % of internal doc links that resolve | `check_doc_links.py` | 100% |
| Claim safety | Number of overclaiming phrases | `check_claims.py` | 0 |
| Index coverage | % of docs linked from PROJECT_INDEX.md | Manual audit | 100% |
| Freshness | Age since last significant update | `git log` | < 6 months |
| Onboarding time | Time from clone to demo | Stopwatch | < 15 min |
| Concept card coverage | % of artifact types with cards | Manual audit | 100% |

## Related

- `docs/evidence/DOCS_READINESS_CHECKLIST.md` — per-release checklist
- `docs/evidence/DOCS_REVIEW_CADENCE_POLICY.md` — review schedule
