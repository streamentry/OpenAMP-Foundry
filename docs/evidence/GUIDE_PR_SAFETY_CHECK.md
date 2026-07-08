# PR Template Check for Safety-Sensitive Files

PRs that modify safety-sensitive files require additional checks.

## Safety-Sensitive Files
- `SAFETY.md`
- `RESPONSIBLE_USE.md`
- `docs/trust/*`
- `AGENTS.md`
- `configs/recalibration_policy.yaml`
- `configs/pipeline.yaml`

## Required Checks
- [ ] Change has been reviewed by a safety reviewer.
- [ ] No overclaiming language introduced (run `check_claims.py`).
- [ ] Safety implications documented in PR description.
- [ ] All existing safety tests pass.

## Enforcement
- PR template should include a section for safety-sensitive changes.
- CI should flag PRs that touch safety-sensitive files without a safety reviewer.
