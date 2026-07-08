# PR Review Rubric by Risk Class

How to review PRs based on their risk level.

| Risk Class | Examples | Review Required | Review Depth |
|------------|----------|:---------------:|:------------:|
| Low | Typo fixes, formatting, docs | 1 maintainer | Surface-level |
| Medium | New tests, minor features | 1 maintainer | Functional review |
| High | Policy changes, safety, calibration | 2 maintainers | Deep review |
| Critical | Release, security, safety policy | 3 maintainers + project lead | Full audit |

## Low-Risk Review Checklist

- [ ] Tests pass
- [ ] No overclaiming language
- [ ] No broken links

## High-Risk Review Checklist (all of the above plus)

- [ ] Design doc or RFC exists
- [ ] Safety implications reviewed
- [ ] Backward compatibility considered
- [ ] Rollback plan documented
