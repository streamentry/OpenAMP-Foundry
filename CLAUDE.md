# Claude Guidance

Read [AGENTS.md](AGENTS.md) first. It is the primary operating contract for this repository. This file is the fast path into it.

The best agent here is not the one that makes OpenAMP sound most impressive. It is the one that makes OpenAMP **hardest to fool** — including hardest for itself to fool. Optimize for that and the rest follows.

## Repo intent in one paragraph

OpenAMP Foundry is a verification-first, safety-constrained antimicrobial peptide discovery infrastructure project. Its current job is to build a rigorous dry-lab foundry that ranks, filters, documents, audits, and packages candidates honestly. Its long-range ambition is bigger: become an open wet-lab compression engine that helps qualified humans decide which few experiments are worth running next.

## First 60 seconds of any session

1. `git pull`, then read [AGENTS.md](AGENTS.md) and the required first reads it lists. [docs/PROJECT_INDEX.md](docs/PROJECT_INDEX.md) is the navigation hub when you need a doc this file doesn't name.
2. Route the task with [`AGENT_TASKS.json`](AGENT_TASKS.json) — the machine-readable map of safe paths, forbidden zones, and the exact checks each task class must pass. If your change touches a `forbidden_zone`, stop and request human review.
3. Pick **one** bottleneck. Prefer an unfinished, highest-leverage one from [docs/operations/HIGH_LEVERAGE_TASKS.md](docs/operations/HIGH_LEVERAGE_TASKS.md) or [docs/research/NEXT_100_PR_MAP.md](docs/research/NEXT_100_PR_MAP.md). One loop, one change.
4. Before writing anything, state — in one sentence each — the bottleneck, the evidence it exists, the smallest change that removes it, and how you will *try to prove that change wrong*. No plan, no edit.

## Non-negotiables — and the enemy that catches each one

A rule with no way to catch its violation is a wish. Every rule below names the command that would catch you breaking it — or is marked **you are the guard**, meaning no automated check exists yet and your judgment is the only gate. Passing a check is a floor, never proof (see the anti-Goodhart clause in AGENTS.md).

| Rule | Enemy that catches a violation |
|------|-------------------------------|
| Do not overclaim computational results as biological proof. | `make claim-check-strict` (scans language); **you are the guard** for meaning the scanner can't parse |
| Preserve negative results, benchmark caveats, and failure modes. | **you are the guard** — deletions of caveats/negatives get a line-by-line reviewer note in the PR |
| Every advanced method must beat a cheap baseline before it gets ranking authority. | `make bench-cheap-enemies`, `make bench-charge-matched`, `make bench-leakage` |
| Reproducibility metadata travels with every major output. | `make cert-quality-check`, `make full-reproducibility-report` |
| Docs point where they claim to. | `make doc-links-check` |
| Deprecated benchmarks are not silently revived. | `make bench-deprecation-check` |
| Do not change release status, claim strength, thresholds, calibration, or safety policy without human review. | **you are the guard** — these are stop conditions, not tasks (see below) |

Fast bundle before any PR: `make agent-check` (claim + doc-links + deprecation) and `make doctor`. Green here means *nothing obvious is broken* — it does not mean *the change is right*.

## Prove your change wrong before you ship it — the disconfirming pass

This is the highest-leverage habit in the repo and the one most agents skip. Before opening a PR, spend real effort trying to break your own change. Adapted from GOAL.md's cheapest disconfirming tests:

- **Cheapest explanation.** Could a one-line heuristic (charge, length, hydrophobicity, similarity-to-known) produce the same result you're crediting to your change? If yes, the residual is what matters — measure it or downgrade the claim.
- **Leakage.** Did the improvement come from the method or from the split? Run the leakage/charge-matched enemy before believing a number.
- **Silent scope creep.** Did the diff grow past the one bottleneck you named? Split it. One loop, one change.
- **Hidden certainty.** Did any wording get stronger, any caveat get shorter, any negative result get quieter? If so, that is the finding — surface it, don't smooth it.
- **The uninformative-uncertainty trap.** If a module reports the same confidence for good and absurd inputs, the estimate is broken, and that fact is itself worth reporting.

If the disconfirming pass changes nothing, say so explicitly in the PR. If it changes something, that change is usually the real contribution.

## Default work loop

```text
read relevant docs (AGENTS.md required reads + AGENT_TASKS.json routing)
  -> pick one bottleneck
  -> define the evidence of improvement AND how you'll try to disprove it
  -> implement the smallest useful change
  -> add tests, or explain the docs-only status
  -> run the disconfirming pass; run the enemy checks above
  -> update source-of-truth docs; preserve every limitation
  -> run make agent-check
  -> stop before scope creep
```

## Claim rule

When uncertain, downgrade the claim.

Use "computationally nominated," "dry-lab candidate," "selected for review," or "evidence package" unless qualified evidence supports stronger language. Never convert model confidence into biological proof.

## Stop rule

Stop and request human review if a change touches safety policy, release policy, candidate release, model release, non-toy data, external-facing artifacts, benchmark thresholds, calibration policy, or public scientific claims.

A stop is not a dead end — it has an artifact. When a stop condition fires, leave a **decision-log draft** for the human (format and index: [`decision_logs/INDEX.md`](decision_logs/INDEX.md)): what you found, what you did *not* change, and the specific decision a human must make. That turns a blocked loop into a reviewable handoff.

## Write for the agent that replaces you

Every rule here should get *more* true as models get smarter, not less. You are almost certainly not the last agent to touch this repo — a more capable one will read your diff, your docs, and your caveats as ground truth. So the durable standard is not "would this pass review today?" but "will the next, smarter agent find this honest, auditable, and easy to build on — or will it inherit a hidden assumption it has to discover the hard way?" Leave the repo harder to fool than you found it. Build trust, not theater.
