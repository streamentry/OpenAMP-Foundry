# Maintainer Runbook: Unsafe Claim Wording

When unsafe claim wording is found:

1. Run `python scripts/safety/check_claims.py` to see all flagged phrases.
2. Review each flagged phrase in context.
3. Rewrite overclaiming phrases using project-allowed terms.
4. If the claim is in a public-facing document, prioritize the fix.
5. Re-run the check to confirm the fix.
6. If the author disagrees, escalate to maintainers.
