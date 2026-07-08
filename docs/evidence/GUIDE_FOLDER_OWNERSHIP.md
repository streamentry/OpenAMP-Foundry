# Folder Ownership Guide

Each top-level directory has an owner responsible for its content.

| Path | Owner | Review Required |
|------|-------|:---------------:|
| `src/` | Maintainer | Yes |
| `tests/` | Maintainer | Yes |
| `docs/` | Maintainer | For new docs |
| `configs/` | Maintainer | Yes |
| `schemas/` | Maintainer | Yes |
| `scripts/` | Maintainer | For new scripts |
| `examples/` | Contributor | No |
| `outputs/` | Generated | N/A (git-ignored) |

## Rules
- Changes outside the owned path require the path owner's review.
- If no owner is listed for a path, the default owner is the project lead.
- Ownership can be delegated but must be documented.
