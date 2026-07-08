# Docs PR Description Template Guide

How to write good PR descriptions for documentation changes.

## Recommended Format
```markdown
## Change
Brief description of what changed.

## Why
Why the change was needed.

## Related Issues
Closes #NNN

## Verification
- [ ] `python scripts/check_doc_links.py` — 0 broken links
- [ ] `python scripts/safety/check_claims.py` — 0 overclaiming
- [ ] `python3 -m pytest -q` — all tests pass
```

## Rules
- Link to the related issue using "Closes #NNN".
- List what verification you performed.
- Keep the description focused on what changed, not how.
