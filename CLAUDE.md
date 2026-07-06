# Claude Guidance

Read [AGENTS.md](AGENTS.md) first. It is the primary operating contract for this repository.

## Repo intent in one paragraph

OpenAMP Foundry is a verification-first, safety-constrained antimicrobial peptide discovery infrastructure project. Its current job is to build a rigorous dry-lab foundry that ranks, filters, documents, audits, and packages candidates honestly. Its long-range ambition is bigger: become an open wet-lab compression engine that helps qualified humans decide which few experiments are worth running next.

## Non-negotiables

- Do not overclaim computational results as biological proof.
- Preserve negative results, benchmark caveats, and failure modes.
- Protect the repo’s dry-lab and safety boundaries.
- Prefer reproducibility, calibration, and honest uncertainty over impressive language.
- Treat any virtual-assay or simulation layer as experimental until it clearly improves decision quality.
- Compare advanced methods against cheap baselines before trusting them.
- Make every meaningful change easier for the next human or agent to audit.
- Do not change release status, claim strength, benchmark thresholds, or safety policy without human review.

## Fast orientation

- [docs/PROJECT_INDEX.md](docs/PROJECT_INDEX.md) — navigation hub for humans and agents.
- [docs/TRUST_CENTER.md](docs/TRUST_CENTER.md) — trust architecture.
- [docs/COMMAND_SURFACE.md](docs/COMMAND_SURFACE.md) — command workflows and claim boundaries.
- [docs/HUMAN_AGENT_COLLABORATION.md](docs/HUMAN_AGENT_COLLABORATION.md) — human-agent division of labor.
- [docs/REVIEWER_ONBOARDING.md](docs/REVIEWER_ONBOARDING.md) — review expectations.
- [docs/NEXT_100_PR_MAP.md](docs/NEXT_100_PR_MAP.md) — PR-sized backlog.
- [docs/PROOF_LADDER.md](docs/PROOF_LADDER.md) — claim ladder and evidence levels.

## Key docs

- [README.md](README.md)
- [VISION.md](VISION.md)
- [GOAL.md](GOAL.md)
- [MISSION.md](MISSION.md)
- [GOVERNANCE.md](GOVERNANCE.md)
- [AGENTS.md](AGENTS.md)
- [SAFETY.md](SAFETY.md)
- [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md)
- [MODEL_RELEASE_POLICY.md](MODEL_RELEASE_POLICY.md)
- [DATA_LICENSE_NOTICE.md](DATA_LICENSE_NOTICE.md)
- [docs/ARTIFACT_VERSIONING.md](docs/ARTIFACT_VERSIONING.md)
- [docs/BENCHMARK_GOVERNANCE.md](docs/BENCHMARK_GOVERNANCE.md)
- [docs/CI_AND_QUALITY_GATES.md](docs/CI_AND_QUALITY_GATES.md)
- [docs/CLAIM_REVIEW_CHECKLIST.md](docs/CLAIM_REVIEW_CHECKLIST.md)
- [docs/DATA_GOVERNANCE.md](docs/DATA_GOVERNANCE.md)
- [docs/MODEL_CARD_TEMPLATE.md](docs/MODEL_CARD_TEMPLATE.md)
- [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)

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

Use “computationally nominated,” “dry-lab candidate,” “selected for review,” or “evidence package” unless qualified evidence supports stronger language.

Never convert model confidence into biological proof.

## Stop rule

Stop and request human review if a change touches safety policy, release policy, candidate release, model release, non-toy data, external-facing artifacts, benchmark thresholds, calibration policy, or public scientific claims.
