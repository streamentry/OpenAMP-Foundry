# Release Candidate Checklist Artifact

Artifacts that should exist before a release candidate is declared.

## Checklist
- [ ] `make full-reproducibility-report` succeeds
- [ ] `python scripts/check_doc_links.py` — 0 broken links
- [ ] `python scripts/safety/check_claims.py` — 0 overclaiming
- [ ] `python3 -m pytest -q` — all tests pass
- [ ] PUBLICATION_PACK.md checklist is complete
- [ ] METRICS_CURRENT.md is up to date
- [ ] Evidence certificates are regenerated
- [ ] Lab batch pack is built (`make lab-batch-pack`)
- [ ] Decision log is current
- [ ] Limitations overview is accurate

## Related
- `docs/review/PUBLICATION_PACK.md`
- `docs/evidence/DOCS_READINESS_CHECKLIST.md`
