# Documentation Role Definitions

Defines who is responsible for what in the documentation system.

## Roles

| Role | Responsibilities | Required For |
|------|------------------|--------------|
| **Contributor** | Fix typos, update examples, add tests for docs | All changes |
| **Reviewer** | Verify accuracy, completeness, and claim wording | PRs with policy changes |
| **Maintainer** | Own doc structure, approve new docs, enforce standards | New document creation |
| **Safety reviewer** | Verify safety docs are accurate and current | Safety policy changes |
| **Project lead** | Own documentation vision and license | Structural changes |

## How Roles Map to GitHub

- Contributor = anyone with a GitHub account
- Reviewer = project maintainer or delegated reviewer
- Maintainer = GitHub team with write access
- Safety reviewer = designated safety maintainer
- Project lead = repository owner
