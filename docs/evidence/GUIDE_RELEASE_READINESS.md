# Decision Guide: Release Readiness

Before releasing, verify:

- [ ] `make full-reproducibility-report` succeeds
- [ ] `python scripts/check_doc_links.py` — 0 broken links
- [ ] `python scripts/safety/check_claims.py` — 0 overclaiming
- [ ] `python3 -m pytest -q` — all tests pass
- [ ] METRICS_CURRENT.md is up to date
- [ ] PUBLICATION_PACK.md checklist is complete
- [ ] Decision log is current

## Decision
- All checks pass → Release candidate
- Minor issues → Fix before release
- Major issues → Block release
