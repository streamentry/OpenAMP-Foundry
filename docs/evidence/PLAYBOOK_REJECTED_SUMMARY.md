# Scenario Playbook: Rejected Public Summary

**Scenario:** A proposed public summary is rejected during review.

## Steps

1. Identify the specific reasons for rejection (overclaiming, missing caveats, unclear audience).
2. Address each reason:
   - Overclaiming: Rewrite using allowed terms from AGENTS.md.
   - Missing caveats: Add charge-domination, no wet-lab data, simulation experimental.
   - Unclear audience: Define who the summary is for.
3. Re-run `python scripts/safety/check_claims.py` to verify no overclaiming.
4. Resubmit for review.
5. If the author disagrees with the rejection, escalate to maintainers.
