## Description

<!-- What does this PR do? Why is it needed? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] New scorer / benchmark
- [ ] Documentation update
- [ ] Safety policy change (requires human review)
- [ ] Infrastructure / CI / tooling

## Safety impact

- [ ] No biological misuse capability added
- [ ] No wet-lab protocol added
- [ ] No harmful optimization objective added
- [ ] No unscreened candidate sequences published
- [ ] No efficacy claims without assay evidence
- [ ] Limitations and failure modes documented
- [ ] Evidence is reproducible (run includes seed, commit, config)

## Verification

- [ ] `make ci` passes
- [ ] `make bench-gate` passes (no AUROC regression)
- [ ] Tests added for new functionality
- [ ] Existing tests updated to match any behavior changes
- [ ] Documentation updated if behavior changed
- [ ] Determinism confirmed (`make regenerate-all` if pipeline logic changed)

## Evidence

<!-- For new scorers, benchmarks, or prediction modules: what evidence supports this addition? Include limitation notes. -->

## Dependencies

<!-- List any new dependencies and their license. -->

- None
