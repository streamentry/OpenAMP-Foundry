# Contributor Runbook: Failing Docs Checks

If a docs check fails in CI:

1. Read the error message — it tells you which check failed and why.
2. Run the check locally: `python scripts/check_doc_links.py` or `python scripts/safety/check_claims.py`.
3. Fix the issue (broken link, overclaiming language, etc.).
4. Re-run the check locally to confirm.
5. Push the fix — CI will re-run automatically.
