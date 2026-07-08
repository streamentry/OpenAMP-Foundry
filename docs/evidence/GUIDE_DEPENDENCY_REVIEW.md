# Dependency Review Guide

How to review dependency changes in PRs.

## Steps
1. Verify the new dependency is necessary for the change.
2. Check the license is compatible with Apache 2.0.
3. Check for known security vulnerabilities.
4. Verify the change works on all supported platforms.
5. Update pyproject.toml and lock file if applicable.
6. Verify tests pass with the new dependency.

## Red Flags
- Dependency added but not used in the PR
- Dependency with a restrictive license
- Dependency with known vulnerabilities
- Major version bump without documented breaking changes
