# Contributor Runbook: Asking for Review

1. Before requesting review:
   - Run `python3 -m pytest -q` — all tests must pass.
   - Run `python scripts/check_doc_links.py` — no broken links.
   - Run `python scripts/safety/check_claims.py` — no overclaiming language.
2. Request review from the relevant maintainer.
3. In your review request, note:
   - What the change does
   - What testing you've done
   - Any areas you're unsure about
4. Respond to review comments promptly.
