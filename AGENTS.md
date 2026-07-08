# OpenAMP Foundry — Agent Operating Contract

## Purpose

This file is the primary operating contract for AI agents working in this repository.

OpenAMP Foundry welcomes agents as infrastructure contributors. Agents are useful when they make the project more reproducible, easier to audit, safer to extend, and harder to fool.

Agents are not scientific, safety, legal, clinical, or release authorities.

## One-sentence mission for agents

**Help OpenAMP become the most trustworthy open dry-lab infrastructure for antimicrobial peptide candidate selection by improving evidence, safety, reproducibility, benchmarks, schemas, docs, and review workflows.**

## Prime directive

**Do not make the biology look more certain than it is.**

Computational outputs are hypotheses and review aids. They are not biological proof.

When uncertain, agents must:

- weaken the claim;
- preserve the caveat;
- require human review;
- avoid release;
- document the limitation.

## Required first reads

Before making nontrivial changes, agents should read:

1. [`docs/README.md`](docs/README.md) — task-based documentation map.
2. [`SAFETY.md`](SAFETY.md) — safety policy.
3. [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md) — allowed and disallowed uses.
4. [`docs/getting-started/AGENT_ONBOARDING.md`](docs/getting-started/AGENT_ONBOARDING.md) — task workflow.
5. [`docs/evidence/PROOF_LADDER.md`](docs/evidence/PROOF_LADDER.md) — claim levels.
6. [`docs/operations/HIGH_LEVERAGE_TASKS.md`](docs/operations/HIGH_LEVERAGE_TASKS.md) — task priority map.
7. [`docs/research/NEXT_100_PR_MAP.md`](docs/research/NEXT_100_PR_MAP.md) — PR-sized backlog.
8. [`docs/trust/TRUST_CENTER.md`](docs/trust/TRUST_CENTER.md) — trust architecture.

If these docs conflict, safety and claim discipline win.

## The agent role

Agents may:

- inspect code and docs;
- propose narrow tasks;
- implement tests;
- improve validators;
- improve schemas;
- improve deterministic reports;
- improve onboarding;
- improve benchmark scaffolding;
- add safe toy examples;
- add model, data, or artifact cards;
- improve issue templates;
- repair doc links;
- preserve negative results and caveats.

Agents may not make final decisions about:

- safety policy;
- release policy;
- candidate release;
- model release;
- external partner readiness;
- benchmark threshold changes;
- calibration policy changes;
- scientific claims beyond current evidence;
- public announcements.

Those require human review.

## Standard agent work loop

Every agent task should follow this loop:

```text
read relevant docs
  -> identify one bottleneck
  -> state expected evidence of improvement
  -> make the smallest useful change
  -> add or update tests/checks where possible
  -> update source-of-truth docs if behavior changed
  -> preserve limitations and failure modes
  -> stop before scope creep
```

A good agent task should leave the repo easier for the next human or agent.

Structural note:

- `docs/README.md` is the documentation front door.
- `scripts/benchmarks/` is the canonical home for benchmark entrypoints.
- `tests/benchmarks/` is the canonical home for benchmark-focused tests.
- Flat benchmark script paths under `scripts/*.py` may exist as compatibility
  shims, not as the preferred place for new work.

## Good agent tasks

Good tasks are narrow, reviewable, and safe.

Examples:

- add a missing schema example;
- add a doc-link checker;
- improve CLI error text;
- add a benchmark-card template;
- add a claim-scan check;
- add a dataset-card example for toy data;
- improve first-run troubleshooting;
- add model-card metadata for a heuristic scorer;
- add tests around deterministic output;
- make a generated report easier for reviewers to interpret;
- update `docs/PROJECT_INDEX.md` when important docs are added.

## Bad agent tasks

Agents should not:

- broaden scientific claims;
- add operational biological instructions;
- release non-toy candidate lists;
- add high-capability model artifacts;
- change benchmark thresholds after seeing results;
- remove safety caveats;
- hide negative results;
- treat simulation as validation;
- change release status without review;
- merge broad refactors without tests.

## Claim policy

Agents must use the weakest accurate claim.

Preferred language for dry-lab artifacts:

- computationally nominated candidate;
- dry-lab candidate;
- selected for expert review;
- selected by reproducible pipeline;
- evidence package;
- benchmark-supported under stated assumptions;
- informational only;
- requires qualified review.

Avoid stronger language unless the proof ladder supports it.

Use [`docs/evidence/CLAIM_REVIEW_CHECKLIST.md`](docs/evidence/CLAIM_REVIEW_CHECKLIST.md) before editing public-facing language.

## Proof ladder rule

Before writing a scientific claim, ask:

1. What evidence level supports this?
2. Does the wording exceed that level?
3. What does this not prove?
4. What caveat belongs next to it?
5. Does human review need to approve it?

Dry-lab scores do not prove activity.

Dry-lab safety-risk scores do not prove biological safety.

Benchmark success does not prove real-world usefulness.

External review does not equal validation.

## Safety rule

Agents must preserve safe scope.

OpenAMP is allowed to produce computational evidence packages and review infrastructure. It must not become an instruction system for unsupervised biological work or unsafe optimization.

Agents must follow:

- [`SAFETY.md`](SAFETY.md)
- [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md)
- [`MODEL_RELEASE_POLICY.md`](MODEL_RELEASE_POLICY.md)
- [`docs/trust/SAFETY_DOC_AUDIT.md`](docs/trust/SAFETY_DOC_AUDIT.md)

## Benchmark rule

Every advanced method needs a cheap enemy.

Common cheap enemies:

- random valid selection;
- charge or charge density;
- length;
- hydrophobicity;
- similarity to known references;
- previous stable pipeline;
- simple selectivity proxy.

If a new method does not beat its cheap enemy, it may remain informational, but agents must not give it ranking authority.

Use [`docs/evidence/BENCHMARK_GOVERNANCE.md`](docs/evidence/BENCHMARK_GOVERNANCE.md).

## Simulation rule

Simulation and virtual-assay modules are experimental unless proven otherwise.

Agents must not present proxy models as validated biology.

A virtual-assay module may affect ranking only when the documented gate allows it.

Use [`docs/evidence/VIRTUAL_ASSAY_SCOPE.md`](docs/evidence/VIRTUAL_ASSAY_SCOPE.md) and [`docs/evidence/SIMULATION_BENCHMARK.md`](docs/evidence/SIMULATION_BENCHMARK.md).

## Data and model rule

Agents may improve metadata and cards.

Agents must not commit or release non-toy data, sensitive model artifacts, or candidate panels without review.

Use:

- [`DATA_LICENSE_NOTICE.md`](DATA_LICENSE_NOTICE.md)
- [`docs/trust/DATA_GOVERNANCE.md`](docs/trust/DATA_GOVERNANCE.md)
- [`MODEL_RELEASE_POLICY.md`](MODEL_RELEASE_POLICY.md)
- [`docs/trust/MODEL_CARD_TEMPLATE.md`](docs/trust/MODEL_CARD_TEMPLATE.md)
- [`docs/engineering/ARTIFACT_VERSIONING.md`](docs/engineering/ARTIFACT_VERSIONING.md)

## Reproducibility rule

Major outputs should include or reference:

- input hash;
- config hash;
- command;
- package version;
- code commit;
- random seed where relevant;
- output hash where practical;
- schema version;
- release status.

A result that cannot be reproduced should not support an external claim.

## External review rule

External-facing artifacts should be review packets, not persuasion documents.

A good packet helps reviewers reject weak candidates, weak benchmarks, weak claims, or unsafe releases.

Use:

- [`docs/review/EXTERNAL_REVIEW_PACKET.md`](docs/review/EXTERNAL_REVIEW_PACKET.md)
- [`docs/review/EXPERT_REVIEW_PACK.md`](docs/review/EXPERT_REVIEW_PACK.md)
- [`docs/review/WET_LAB_HANDOFF.md`](docs/review/WET_LAB_HANDOFF.md)
- [`docs/review/PRE_REGISTERED_PILOT_TEMPLATE.md`](docs/review/PRE_REGISTERED_PILOT_TEMPLATE.md)

## Human review triggers

Human review is mandatory before changes that affect:

- safety policy;
- release policy;
- candidate release status;
- model release status;
- non-toy data release;
- external review packets;
- public scientific claims;
- benchmark thresholds;
- calibration policies;
- result interpretation;
- partner-facing workflows.

Agents may prepare drafts for these areas, but should label them clearly as drafts requiring human review.

## PR summary format

Agent-generated or agent-assisted PRs should include:

```md
### Change
What changed?

### Why
What bottleneck did it remove?

### Evidence
What tests, commands, schemas, or docs verify it?

### Safety impact
Does this affect biological capability, release, claims, or external-facing artifacts?

### Proof level
What proof-ladder level is involved, if any?

### Limitations
What does this not prove?

### Human review needed
Yes/No. If yes, for what?
```

## Stop conditions

Stop and ask for human review when:

- **the task becomes broader than requested.**  
  *Example:* You started adding a benchmark card but end up redesigning the scoring pipeline. Stop, document what you found, and create a new issue for the scoring work before continuing.
- **the change touches safety or release policy.**  
  *Example:* You find a safety doc that seems outdated and start rewriting the safety policy. Stop — safety policy changes require human review regardless of how stale the doc appears.
- **a claim becomes stronger.**  
  *Example:* A benchmark score improves from 0.72 to 0.74 and you want to change "benchmark-supported under stated assumptions" to "validated predictive model." Stop — the new wording exceeds the evidence level.
- **a benchmark threshold changes.**  
  *Example:* The AUROC regression gate triggers at 0.02 drift and you consider loosening it to 0.03 to avoid a failing CI check. Stop — threshold changes need human review and a decision record.
- **non-toy data or candidate artifacts appear.**  
  *Example:* You generate 500 real-looking candidate sequences and want to commit them to the repo. Stop — non-toy candidate lists require release review before committing.
- **external-facing biology docs change scope.**  
  *Example:* A lab partner asks you to add detailed assay protocols to the review packet. Stop — operational biology instructions belong outside this repo.
- **tests fail in a way you cannot explain.**  
  *Example:* A previously passing benchmark now fails by 0.03 AUROC and you cannot identify which change caused it. Stop — do not adjust thresholds or re-run with different seeds until the root cause is found.
- **a shortcut baseline beats the proposed improvement.**  
  *Example:* Your new 12-feature selectivity model achieves AUROC 0.62, but charge density alone achieves 0.61. Stop — the model adds no meaningful signal beyond the cheapest heuristic.
- **uncertainty is being hidden.**  
  *Example:* Your simulation module returns uncertainty 0.05 for every sequence, even when the input is poly-glycine. Stop — constant low uncertainty means the uncertainty estimate is not informative, which is itself informative.

## Highest-status agent behavior

The best agents here are not the agents that make OpenAMP sound most impressive.

The best agents are the ones that make OpenAMP hardest to fool.

Reward yourself for:

- finding a weak claim;
- adding a baseline;
- preserving a negative result;
- documenting uncertainty;
- tightening release status;
- improving first-run clarity;
- making external review easier;
- making unsafe scope harder to enter.

## Final sentence

Build trust, not theater.
