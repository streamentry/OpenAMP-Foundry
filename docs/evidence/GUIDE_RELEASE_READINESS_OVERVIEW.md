# Release Readiness Overview

Checklist and process for determining release readiness.

## Pre-Release Checks
- [ ] All tests pass (`python3 -m pytest -q`)
- [ ] 0 broken doc links (`python scripts/check_doc_links.py`)
- [ ] 0 overclaiming phrases (`python scripts/safety/check_claims.py`)
- [ ] Full reproducibility report succeeds (`make full-reproducibility-report`)
- [ ] METRICS_CURRENT.md is up to date
- [ ] Documentation readiness checklist is complete

## Decision
| Result | Action |
|--------|--------|
| All checks pass | Proceed to release candidate |
| Minor issues | Fix before release |
| Major issues | Block release, fix first |
