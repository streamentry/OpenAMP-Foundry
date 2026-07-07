# Metric Guide: Release Readiness

**Question:** Is the project ready for a public release?

**What to track:** Whether all release artifacts exist and pass checks.

**Artifacts to check:**
- `make full-reproducibility-report` succeeds
- `python scripts/check_doc_links.py` reports 0 broken links
- `python scripts/safety/check_claims.py` — no overclaiming language
- `docs/review/PUBLICATION_PACK.md` checklist is complete

**Target:** All checks pass.

**What good looks like:** A maintainer can run `make full-reproducibility-report`, review the output, and decide whether to proceed.
