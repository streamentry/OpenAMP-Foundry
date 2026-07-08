# Guided Walkthrough: Review Packets

## Scenario
You need to prepare a review packet for an external expert.

## Steps
1. Collect the evidence certificates for selected candidates.
2. Run: `make lab-batch-pack` to create a zip with all artifacts.
3. Include LIMITATIONS_OVERVIEW.md for honest caveats.
4. Include METRICS_CURRENT.md for benchmark context.
5. Include the specific claim or question being reviewed.
6. Run `python scripts/safety/check_claims.py` on all documents.
7. Send the packet with a clear description of what feedback is needed.
