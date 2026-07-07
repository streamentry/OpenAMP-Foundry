# Release Status Concept Card

Defines what each release status means for downstream consumers.

---

## Statuses

| Status | Meaning | Can be cited? | Can be shared? |
|--------|---------|:-------------:|:--------------:|
| **Draft** | Work in progress, may change without notice | No | Internally only |
| **Internal** | Reviewed within the project team | With caveats | Within project |
| **Review-only** | Shared with qualified reviewers | In review context | With reviewers |
| **Public-safe** | Safe for public sharing | Yes, with limitations | Publicly |
| **Restricted** | Contains sensitive information | No | Authorized only |
| **Archived** | Superseded but preserved for reference | As historical | Yes, as-is |
| **Deprecated** | No longer maintained or recommended | Do not cite | Avoid |

## Common Mistakes

| Mistake | Correction |
|---------|------------|
| Citing a Draft as evidence | Use "Internal" or higher |
| Sharing Review-only publicly | Wait for "Public-safe" status |
| Treating Archived as current | Check for superseding document |
| Ignoring Restricted labels | Review access permissions |

## Related

- `docs/trust/RELEASE_CHECKLIST.md` — release process
- `docs/review/PUBLICATION_PACK.md` — publication preparation
