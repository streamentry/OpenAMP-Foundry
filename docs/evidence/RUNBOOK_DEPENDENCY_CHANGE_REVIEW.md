# Maintainer Runbook: Dependency Change Review

When a dependency changes:

1. Verify the new dependency is necessary (not scope creep).
2. Check the license is compatible with Apache 2.0.
3. Check for known vulnerabilities.
4. Verify the change works on all supported platforms.
5. Update pyproject.toml and lock file if applicable.
6. Update any docs that reference the old dependency.
