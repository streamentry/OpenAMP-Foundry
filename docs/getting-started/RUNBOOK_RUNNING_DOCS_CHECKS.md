# Contributor Runbook: Running Docs Checks

Before submitting a PR, always run:

```bash
python scripts/check_doc_links.py   # check for broken links
python scripts/safety/check_claims.py  # check for overclaiming language
```

Fix any issues before requesting review.
