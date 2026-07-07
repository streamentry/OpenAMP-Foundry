# Scenario Playbook: Overclaim Review

**Scenario:** A reviewer flags overclaiming language in a PR.

## Steps

1. Run `python scripts/safety/check_claims.py` to see all flagged phrases.
2. For each flagged phrase, determine if it's a genuine overclaim or an allowed exception.
3. Rewrite overclaiming phrases using the project's allowed terms:
   - "computationally nominated candidate" (not "drug candidate")
   - "predicted antimicrobial peptide" (not "proven antimicrobial")
   - "selected by reproducible pipeline" (not "validated by computation")
4. Re-run the claim scanner to verify the fix.
5. If the original author disagrees with a flag, document the reasoning.
