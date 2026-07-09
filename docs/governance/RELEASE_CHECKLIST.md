# Release Checklist

> **Cross-reference:** The canonical release checklist lives at
> [`docs/trust/RELEASE_CHECKLIST.md`](../trust/RELEASE_CHECKLIST.md).
> This file defines the **programmatic gate structure** enforced by
> `release_gate.py`. Both documents must be kept in sync.

## Pre-release gates

All of the following must pass before any external release:

- [ ] All CI tests pass (`make test`)
- [ ] `agent-check` passes (`make agent-check`)
- [ ] No CRITICAL or HIGH issues in code review
- [ ] Evidence level <= 4 for dry-lab-only artifacts
- [ ] `dry_lab_only=True` confirmed on all artifacts
- [ ] Safety flags reviewed by human
- [ ] Data license verified for all external data used
- [ ] Artifact schema compatibility check passes
- [ ] Adapter declarations validated
- [ ] No hardcoded credentials or secrets

## Release type gates

Each release type has additional gates:

### Candidate release
- [ ] Evidence level checked and documented
- [ ] Human review complete
- [ ] Proof-ladder level verified

### Model release
- [ ] Model card present
- [ ] Baseline comparison present
- [ ] Human sign-off obtained

### Dataset release
- [ ] Data governance sign-off obtained
- [ ] License declaration present

### Evidence packet release
- [ ] All H-phase discipline checks pass
- [ ] Provenance hash present and verified

### Schema release
- [ ] Schema compatibility check passes
- [ ] Version bumped
- [ ] Changelog updated

## Post-release checklist

- [ ] CHANGELOG updated
- [ ] Version bumped in METRICS_CURRENT.md
- [ ] PR merged and main branch pulled
- [ ] Release tagged in git
