# Contributor Runbook: Finishing a Docs PR

Before marking a docs PR as ready:

1. Run `python scripts/check_doc_links.py` — 0 broken links.
2. Run `python scripts/safety/check_claims.py` — no overclaiming.
3. Run `python3 -m pytest -q` — all tests pass.
4. Verify any new docs are linked from PROJECT_INDEX.md.
5. Request review from a maintainer.
