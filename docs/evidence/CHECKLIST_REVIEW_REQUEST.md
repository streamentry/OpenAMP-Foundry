# Review Request Checklist

Before requesting a review, ensure:

- [ ] All tests pass (`python3 -m pytest -q`)
- [ ] No broken doc links (`python scripts/check_doc_links.py`)
- [ ] No overclaiming language (`python scripts/safety/check_claims.py`)
- [ ] PR description explains what changed and why
- [ ] PR references the related issue
- [ ] Changes are limited to the scope described in the PR
