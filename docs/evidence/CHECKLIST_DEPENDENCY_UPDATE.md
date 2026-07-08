# Dependency Update Checklist

Steps for updating a dependency.

- [ ] Check the new version's changelog for breaking changes.
- [ ] Update the version in pyproject.toml.
- [ ] Run `pip install -e ".[dev]"` to install the update.
- [ ] Run `python3 -m pytest -q` to verify nothing is broken.
- [ ] If tests fail, fix compatibility issues.
- [ ] Update any documentation that references the old version.
- [ ] If the dependency has a security fix, note it in the PR.

## Frequency
- Security updates: apply within 1 week.
- Minor updates: apply within 1 month.
- Major updates: evaluate on a case-by-case basis.
