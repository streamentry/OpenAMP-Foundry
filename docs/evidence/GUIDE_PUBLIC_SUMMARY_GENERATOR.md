# Public Summary Generator for Review Packets

Generates a public summary from review packet contents.

## Inputs
- Evidence certificates for selected candidates
- LIMITATIONS_OVERVIEW.md
- METRICS_CURRENT.md (summary)
- The specific claim being reviewed

## Output Format
```markdown
# Summary: [Claim]

## What Was Done
One paragraph description.

## Key Results
- Metric: value
- Key finding: statement

## Limitations
- Known caveat 1
- Known caveat 2

## Next Steps
- What happens next.
```

## Rules
- The summary must not overclaim.
- Run `check_claims.py` on the generated summary.
- Limitations should be as prominent as results.
- The summary should be understandable by a non-specialist.
