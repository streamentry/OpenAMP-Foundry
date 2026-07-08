# Release Notes Generator from Local Metadata

How release notes are generated.

## Current Process
Release notes are written manually at release time, following the
format in `docs/evidence/GUIDE_RELEASE_NOTES_WRITING.md`.

## Metadata Sources
- Git log: `git log --oneline --no-decorate v0.5.N-1..HEAD`
- GitHub issues: `gh issue list --state closed --milestone "v0.5.N"`
- GitHub PRs: `gh pr list --state merged --base main`

## Manual Steps
1. Review git log for notable changes.
2. Group changes by type (Added, Changed, Fixed).
3. Write a summary sentence.
4. Review for overclaiming language.

## Status
Release notes are currently written manually. Automation is a future goal.
