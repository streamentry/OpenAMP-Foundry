# Review Packet — Concept Card

A review packet is the set of documents a reviewer needs to evaluate a claim.

## Required Contents

- Candidate list with scores (CSV or JSONL)
- Evidence certificates for selected candidates
- LIMITATIONS_OVERVIEW.md for honest caveats
- METRICS_CURRENT.md for benchmark context
- The specific claim or question being reviewed

## Optional Contents

- Simulation scores (if `--simulation-mode info` was used)
- Expert review template (`.github/ISSUE_TEMPLATE/expert_review.yml`)

## Rules

- Review packets must not overclaim.
- Review packets must state what evidence is computational vs biological.
- Reviewers must be told this is a dry-lab nomination only.
