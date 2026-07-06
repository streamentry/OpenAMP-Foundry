# Contributing

Thank you for considering a contribution to OpenAMP Foundry.

This project is a **safety-first, verification-driven** antimicrobial peptide discovery foundry. It exists to accelerate responsible antimicrobial discovery — not to enable misuse, overclaim, or publish unvalidated results.

Before contributing, read:

- [SAFETY.md](SAFETY.md) — safety posture and disallowed contributions
- [AGENTS.md](AGENTS.md) — operating principles, claim policy, and kill criteria
- [README.md](README.md) — project scope and quickstart
- [docs/PROJECT_INDEX.md](docs/PROJECT_INDEX.md) — navigation hub for humans and agents
- [docs/HUMAN_ONBOARDING.md](docs/HUMAN_ONBOARDING.md) — human contributor path
- [docs/HIGH_LEVERAGE_TASKS.md](docs/HIGH_LEVERAGE_TASKS.md) — task map by leverage and risk

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
| Documentation improvement | Low-Medium | Clarifies scope, evidence, onboarding, or safety without overclaiming |
| New feature | Medium | Tests, docs update, safety impact note |
| New scorer/benchmark | Medium-High | Limitation documentation, evidence of honesty checks: leakage, overfitting, cheap baselines |
| Safety policy | High | Human review required before merging |
| Wet-lab data / sequences | High | Must be pre-approved; never publish unsafe data |

## What high-leverage contributions look like

High-leverage work usually improves at least one of these:

1. **Trust** — stronger evidence, reproducibility, auditability, or safety.
2. **Decision quality** — better selection of scarce experiment slots.
3. **Interoperability** — cleaner schemas, adapters, manifests, or CLI paths.
4. **External usefulness** — easier onboarding for labs, scientists, engineers, and reviewers.
5. **Compounding** — changes that make future agents and humans faster without lowering standards.

See [docs/HIGH_LEVERAGE_TASKS.md](docs/HIGH_LEVERAGE_TASKS.md) for concrete task categories.

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

Use [docs/PROOF_LADDER.md](docs/PROOF_LADDER.md) to map claim strength to evidence level.

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
7. **Baseline comparison** — if adding a scorer, predictor, simulation module, or selection heuristic.

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

## Evidence note

For scorer, benchmark, adapter, simulation, calibration, or selection changes, include:

```md
### Evidence
- Relevant command(s):
- Test(s) added/updated:
- Cheap baseline compared:
- Result:
- Known caveat:
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
- Prefer adding detailed new guidance under `docs/` unless a top-level file is explicitly part of the primary onboarding surface.
- Keep [docs/PROJECT_INDEX.md](docs/PROJECT_INDEX.md) updated when adding important documents.

## Review process

1. Automated checks must pass (lint, tests, benchmark gate).
2. At least one human review is required for safety-significant changes.
3. PRs that add new scorers or benchmarks need extra scrutiny for honesty and leakage.
4. PRs that affect candidate publication, safety boundaries, or wet-lab-facing artifacts need safety review.
5. PRs may be rejected if they fail the safety impact check.

## Getting help

- Open an issue for questions about the contribution process.
- For safety questions, note them explicitly in the issue.
- Read AGENTS.md for the full operating principles and decision rules.
- Read [docs/PROJECT_INDEX.md](docs/PROJECT_INDEX.md) if you are unsure where a topic belongs.
