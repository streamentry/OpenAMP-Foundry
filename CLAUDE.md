# Claude Guidance

Read [AGENTS.md](AGENTS.md) first. It is the primary operating contract for this repository.

## Repo intent in one paragraph

OpenAMP Foundry is a verification-first, safety-constrained antimicrobial peptide discovery project. Its current job is to build a rigorous dry-lab foundry that ranks, filters, documents, and audits candidates honestly. Its long-range ambition is bigger: become an open **wet-lab compression engine** that helps qualified humans decide which few experiments are worth running next.

## Non-negotiables

- Do not overclaim computational results as biological proof.
- Preserve negative results, benchmark caveats, and failure modes.
- Protect the repo’s dry-lab and dual-use safety boundaries.
- Prefer reproducibility, calibration, and honest uncertainty over impressive language.
- Treat any virtual-assay or simulation layer as experimental until it clearly improves decision quality.
- Compare advanced methods against cheap baselines before trusting them.
- Make every meaningful change easier for the next human or agent to audit.

## Fast orientation

- [docs/PROJECT_INDEX.md](docs/PROJECT_INDEX.md) — navigation hub for humans and agents.
- [docs/AGENT_ONBOARDING.md](docs/AGENT_ONBOARDING.md) — agent task protocol and anti-patterns.
- [docs/HIGH_LEVERAGE_TASKS.md](docs/HIGH_LEVERAGE_TASKS.md) — task map by leverage and risk.
- [docs/PROOF_LADDER.md](docs/PROOF_LADDER.md) — claim ladder and evidence levels.

## Key docs

- [VISION.md](VISION.md)
- [GOAL.md](GOAL.md)
- [MISSION.md](MISSION.md)
- [README.md](README.md)
- [AGENTS.md](AGENTS.md)
- [SAFETY.md](SAFETY.md)
- [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md)
- [MODEL_RELEASE_POLICY.md](MODEL_RELEASE_POLICY.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/BENCHMARKING.md](docs/BENCHMARKING.md)
- [docs/METRICS_CURRENT.md](docs/METRICS_CURRENT.md)
- [docs/DECISION_RULES.md](docs/DECISION_RULES.md)
- [docs/PLAN.md](docs/PLAN.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)
- [docs/COLLABORATION_PLAYBOOK.md](docs/COLLABORATION_PLAYBOOK.md)

## Default work loop

```text
read relevant docs
  -> pick one bottleneck
  -> define evidence of improvement
  -> implement smallest useful change
  -> add tests or explain docs-only status
  -> update source-of-truth docs
  -> preserve limitations
  -> stop before scope creep
```

## Claim rule

When uncertain, downgrade the claim.

Use “computationally nominated,” “dry-lab candidate,” “selected for review,” or “evidence package” unless qualified experimental evidence supports stronger language.

Never convert model confidence into biological proof.
