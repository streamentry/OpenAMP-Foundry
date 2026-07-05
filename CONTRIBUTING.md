# Contributing

Thank you for considering a contribution to OpenAMP Foundry.

This project is a **safety-first, verification-driven** antimicrobial peptide discovery foundry. It exists to accelerate responsible antimicrobial discovery — not to enable misuse, overclaim, or publish unvalidated results.

Before contributing, read:
- [SAFETY.md](SAFETY.md) — safety posture and disallowed contributions
- [AGENTS.md](AGENTS.md) — operating principles, claim policy, and kill criteria
- [README.md](README.md) — project scope and quickstart

## Quickstart for contributors

```bash
make install    # create .venv and install package + dev deps
make demo       # run the demo pipeline
make test       # run all tests
make ci         # run full CI suite (lint + test + benchmark gate)
make bench-gate # run benchmark regression check
```

If all targets pass, your dev environment is ready.

## Types of contributions

| Type | Impact | Expectations |
|------|--------|-------------|
| Bug fix | Low | Tests demonstrating the bug, fix, no regressions |
| New feature | Medium | Tests, docs update, safety impact note |
| New scorer/benchmark | Medium-High | Limitation documentation, evidence of honesty checks (leakage, overfitting) |
| Safety policy | High | Human review required before merging |
| Wet-lab data / sequences | High | Must be pre-approved; never publish unsafe data |

## Claim policy

When contributing documentation or commit messages, follow these rules:

**Allowed:**
- "Computationally nominated candidate"
- "Predicted antimicrobial peptide"
- "Dry-lab candidate"
- "Selected by reproducible pipeline"
- "Novel candidate family" (if novelty analysis supports it)

**Forbidden unless experimentally proven:**
- "AI discovered an antibiotic"
- "Drug candidate"
- "Safe", "Effective in humans", "Clinically useful"
- "Cure", "Breakthrough therapy"
- "Proven antimicrobial" (before lab validation)
- "World-first" (unless independently verified)

## Before opening a PR

1. Run `make ci` and confirm all gates pass.
2. Run `make bench-gate` and confirm AUROC has not regressed.
3. If you changed pipeline logic, run `make regenerate-all` to verify determinism.
4. Add tests for new functionality. Aim for >80% coverage on new code.
5. Update docs if behavior changes.
6. Add a safety impact note to the PR description (see template below).
7. Check that your contribution doesn't add any prohibited content:
   - Toxicity-maximizing objectives
   - Instructions for culturing or modifying pathogens
   - High-risk assay protocols
   - Unscreened candidate dumps
   - Evasion of safety filters
   - Claims of efficacy without assay evidence
   - Clinical or medical advice

## PR requirements

Every PR must include:

1. **Clear scope** — what it does and why.
2. **Tests** — new or updated tests that cover the change.
3. **Documentation update** — if behavior changes.
4. **Safety impact note** — filled out checklist (see below).
5. **License status** — for any new data or model dependency.
6. **Limitations** — if adding a scorer, benchmark, or prediction module.

## Safety impact note

Copy this into your PR description:

```md
### Safety impact
- [ ] No biological misuse capability added
- [ ] No wet-lab protocol added
- [ ] No harmful optimization objective added
- [ ] No unscreened candidate sequences published
- [ ] No efficacy claims without assay evidence
- [ ] Limitations and failure modes documented
- [ ] Evidence is reproducible (run includes seed, commit, config)
```

## Code standards

- Follow existing patterns in the codebase (see AGENTS.md section on code style).
- Use existing libraries — don't add new heavy dependencies unless justified.
- No placeholder or TODO comments in production code.
- Keep functions small and single-purpose.
- Preserve negative results, failure modes, and honest limitations.
- Never optimize for mammalian toxicity, pathogen enhancement, or immune evasion.

## Documentation policy

- Update docs when behavior changes.
- Document limitations for new scorers, benchmarks, or prediction modules.
- Preserve negative results — a clean failure is more valuable than a fake success.
- Do not create new top-level `.md` files unless explicitly needed.

## Review process

1. Automated checks must pass (lint, tests, benchmark gate).
2. At least one human review is required for safety-significant changes.
3. PRs that add new scorers or benchmarks need extra scrutiny for honesty and leakage.
4. PRs may be rejected if they fail the safety impact check.

## Getting help

- Open an issue for questions about the contribution process.
- For safety questions, note them explicitly in the issue.
- Read AGENTS.md for the full operating principles and decision rules.
