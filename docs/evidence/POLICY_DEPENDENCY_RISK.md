# Dependency Risk Review Policy

How to review dependency risks.

## Risk Levels
| Level | Criteria | Review Required |
|:-----:|----------|:---------------:|
| Low | Well-known library, stable API, permissive license | None |
| Medium | Less common library, breaking changes possible | Maintainer |
| High | New dependency, restrictive license, security-sensitive | Project lead |

## Required Checks
- License compatibility with Apache 2.0
- Known security vulnerabilities
- Maintenance status (recent releases, issue response)
- Number of transitive dependencies

## Prohibited
- Dependencies with GPL or AGPL licenses (unless absolutely necessary and reviewed)
- Dependencies with known critical vulnerabilities
- Unmaintained dependencies (no release in > 2 years)
