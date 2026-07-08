# Reviewer Role Taxonomy

Defines reviewer roles and their responsibilities.

| Role | Can Approve | Required For | Review Depth |
|------|:-----------:|--------------|:------------:|
| Contributor | No | All PRs | Comment only |
| Reviewer | Low-risk | Medium-risk PRs | Functional |
| Maintainer | High-risk | High-risk PRs | Deep |
| Safety reviewer | Safety changes | Safety-sensitive files | Full audit |
| Project lead | All | Final approval | Final |

## Assignment
- Reviewers should be assigned based on expertise.
- Safety changes always need a safety reviewer.
- High-risk changes need at least 2 reviewers.
- The project lead has final authority on disputes.
