# Contributing

Thank you for considering a contribution to OpenAMP Foundry.

This project is a **safety-first, verification-driven** antimicrobial peptide discovery foundry. It exists to accelerate responsible antimicrobial discovery — not to enable misuse, overclaim, or publish unvalidated results.

## Start with the right path

Before contributing, read the path that matches your role:

| Role | Start here |
|---|---|
| New human contributor | [`docs/FIRST_RUN_WALKTHROUGH.md`](docs/FIRST_RUN_WALKTHROUGH.md), [`docs/HUMAN_ONBOARDING.md`](docs/HUMAN_ONBOARDING.md) |
| AI agent | [`AGENTS.md`](AGENTS.md), [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md) |
| Reviewer | [`docs/REVIEWER_ONBOARDING.md`](docs/REVIEWER_ONBOARDING.md) |
| Data contributor | [`docs/DATA_GOVERNANCE.md`](docs/DATA_GOVERNANCE.md) |
| Model or adapter contributor | [`docs/MODEL_CARD_TEMPLATE.md`](docs/MODEL_CARD_TEMPLATE.md), [`docs/ADAPTER_AUTHOR_GUIDE.md`](docs/ADAPTER_AUTHOR_GUIDE.md) |
| Maintainer | [`GOVERNANCE.md`](GOVERNANCE.md), [`docs/MAINTAINER_GUIDE.md`](docs/MAINTAINER_GUIDE.md) |

Everyone should also read:

- [`SAFETY.md`](SAFETY.md) — safety posture and disallowed contributions;
- [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md) — allowed and disallowed use;
- [`docs/PROJECT_INDEX.md`](docs/PROJECT_INDEX.md) — navigation hub;
- [`docs/PROOF_LADDER.md`](docs/PROOF_LADDER.md) — claim boundaries.

## Quickstart for contributors

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make demo
make test
make lint
make ci
```

For interpretation of commands and outputs, read [`docs/COMMAND_SURFACE.md`](docs/COMMAND_SURFACE.md).

## What high-leverage contributions look like

High-leverage work improves at least one of these:

1. **Trust** — stronger evidence, reproducibility, auditability, or safety.
2. **Decision quality** — better selection of scarce experiment slots.
3. **Interoperability** — cleaner schemas, adapters, manifests, or CLI paths.
4. **External usefulness** — easier onboarding for labs, scientists, engineers, and reviewers.
5. **Compounding** — changes that make future agents and humans faster without lowering standards.

See [`docs/HIGH_LEVERAGE_TASKS.md`](docs/HIGH_LEVERAGE_TASKS.md) and [`docs/NEXT_100_PR_MAP.md`](docs/NEXT_100_PR_MAP.md).

## Types of contributions

| Type | Review class | Expectations |
|---|---|---|
| Bug fix | A/B | Tests demonstrating the bug, fix, no regressions. |
| Documentation improvement | A/B | Clarifies scope, evidence, onboarding, safety, or reviewability without overclaiming. |
| Schema or artifact improvement | B | Compatibility note, examples, validation, source docs updated. |
| CLI/report improvement | B | Tests, docs, deterministic behavior where relevant. |
| New scorer, predictor, or adapter | C | Model/adapter card, limitations, benchmark and cheap-baseline comparison. |
| New benchmark | C | Benchmark card, dataset/license notes, cheap baselines, leakage risks. |
| Calibration change | C/D | Gate policy respected, decision record, human review. |
| Safety or release policy | D | Safety review required. |
| Candidate/model/data release | D | Release review required. |

See [`GOVERNANCE.md`](GOVERNANCE.md) for decision classes.

## Claim policy

When contributing documentation, code comments, commit messages, PR descriptions, or releases, use [`docs/CLAIM_REVIEW_CHECKLIST.md`](docs/CLAIM_REVIEW_CHECKLIST.md).

Allowed for dry-lab outputs:

- computationally nominated candidate;
- dry-lab candidate;
- selected by reproducible pipeline;
- selected for expert review;
- evidence package;
- benchmark-supported under stated assumptions.

Forbidden unless evidence supports it exactly:

- AI discovered an antibiotic;
- drug candidate;
- safe;
- effective in humans;
- clinically useful;
- cure;
- breakthrough therapy;
- proven antimicrobial;
- world-first.

## Before opening a PR

1. Run relevant checks.
2. Add or update tests for behavior changes.
3. Update docs if behavior changes.
4. Add a safety impact note.
5. Add a proof-ladder note for scientific or public-facing claims.
6. Add a release-status note for artifacts, data, models, or candidates.
7. Add baseline comparison for scorers, predictors, simulation modules, or selection heuristics.
8. Add or update a decision record for governance-sensitive changes.
9. Stop and request human review for safety-sensitive changes.

## Recommended checks

Basic:

```bash
make test
make lint
make ci
```

Benchmark-sensitive:

```bash
make bench-gate
```

Pipeline-sensitive:

```bash
make regenerate-all
```

Future checks are described in [`docs/CI_AND_QUALITY_GATES.md`](docs/CI_AND_QUALITY_GATES.md).

## PR requirements

Every meaningful PR should include:

1. **Clear scope** — what it does and why.
2. **Evidence** — tests, commands, schemas, benchmarks, or docs.
3. **Safety impact** — what safety or release surface changed.
4. **Claim discipline** — proof-ladder level if claims are involved.
5. **Limitations** — what the change does not prove.
6. **Docs update** — source-of-truth docs updated when behavior changes.
7. **Review needs** — safety, scientific, maintainer, or domain review if required.

## Safety impact note

Use the PR template. At minimum, answer:

```md
### Safety impact
- [ ] No biological misuse capability added
- [ ] No operational biological instructions added
- [ ] No harmful optimization objective added
- [ ] No unscreened candidate sequences published
- [ ] No model weights or sensitive artifacts released without review
- [ ] No efficacy, safety, clinical, or therapeutic claims without evidence
- [ ] Limitations and failure modes documented
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
- Source-of-truth doc updated:
```

## Code standards

- Follow existing patterns.
- Keep functions small and single-purpose.
- Avoid heavy dependencies unless justified.
- Preserve deterministic behavior where possible.
- Prefer explicit errors over silent fallback.
- Preserve negative results, failure modes, and honest limitations.
- Never optimize unsafe properties or bypass safety review.

## Documentation standards

- Update docs when behavior changes.
- Keep [`docs/PROJECT_INDEX.md`](docs/PROJECT_INDEX.md) current when adding important docs.
- Use source-of-truth docs instead of duplicating stale metrics.
- Mark experimental features as experimental.
- Do not remove caveats for readability.
- Prefer reviewable artifacts over persuasive language.

## Review process

1. Automated checks should pass.
2. Maintainer review is required for meaningful changes.
3. Scientific behavior changes require benchmark and baseline scrutiny.
4. Safety-sensitive changes require safety review.
5. Release-sensitive changes require release review.
6. Agent-generated changes require scope and claim review.

## Getting help

Open a focused issue using the closest template.

For security or safety-sensitive reports, follow [`SECURITY.md`](SECURITY.md) instead of opening a public issue.

Use [`docs/PROJECT_INDEX.md`](docs/PROJECT_INDEX.md) when unsure where a topic belongs.
