# Public Readiness Dry-Run Command

Check if the project is ready for public sharing.

## Usage
```bash
make full-reproducibility-report
python scripts/check_doc_links.py
python scripts/safety/check_claims.py
python3 -m pytest -q
```

## What It Checks
- All tests pass
- No broken doc links
- No overclaiming language
- Reproducibility report succeeds
- Phase 4 artifacts exist

## Exit Codes
| Code | Meaning |
|:----:|---------|
| 0 | Ready for public sharing |
| Non-zero | Check the specific failure |

## Related
- `docs/evidence/GUIDE_PUBLIC_READINESS.md`
- `docs/review/RELEASE_DRY_RUN_GUIDE.md`
