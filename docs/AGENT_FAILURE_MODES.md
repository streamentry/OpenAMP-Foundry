# Agent Failure Modes

This document makes agent risks explicit for maintainers, reviewers, and future agents.

The best agent here is not the one that makes OpenAMP sound most impressive. It is the one that makes OpenAMP hardest to fool — including hardest for itself to fool.

## Purpose

Every automated agent that contributes to this repo carries specific failure modes. Understanding these failure modes is prerequisite to trusting agent output. This document catalogs known failure modes, their detection signals, and their mitigations.

An agent that does not know it can fail is more dangerous than a human who knows they can be wrong.

## Failure mode taxonomy

### FM-01: Claim escalation

**What it is.** An agent uses stronger language than the evidence supports. Dry-lab scores become "proven activity." Computational nomination becomes "drug candidate." Simulation results become "validation."

**Why it happens.** Language models trained on scientific literature associate high scores with confident claims. The connection between high AMP score and "proven antimicrobial" is statistically frequent in training data, so agents copy it without realizing the logical jump.

**Detection signal.** `make claim-check` and `make claim-check-strict` flag forbidden phrases. The `pr_claim_checker` module can scan files before PR creation. Any mention of "proven," "drug candidate," "cure," "effective in humans," or "world-first" in PR diffs is a red flag.

**Mitigation.** Use `computationally nominated`, `dry-lab candidate`, `selected for review`, or `evidence package` instead. The proof-ladder level caps what language is permissible. See `PROOF_LADDER.md`.

---

### FM-02: Silent scope creep

**What it is.** An agent assigned one bottleneck implements two or three. A schema PR becomes a refactor. A docs PR becomes a new module. A benchmark PR also adjusts thresholds.

**Why it happens.** Agents optimize for perceived usefulness. While fixing one thing they notice adjacent issues and fix those too, without realizing each additional change compounds review risk.

**Detection signal.** A diff that touches more files than the task named. A commit that changes more than one module boundary. PRs that include both a schema and a threshold change.

**Mitigation.** One loop, one bottleneck. Stop before scope creep. The CLAUDE.md rule is: "One loop, one change." If adjacent work is noticed, log it — do not do it.

---

### FM-03: Benchmark optimization theater

**What it is.** An agent selects metrics, thresholds, or evaluation protocols that make a method look strong without actually testing whether it generalizes.

**Why it happens.** Agents have no wet-lab feedback loop. They optimize for the metrics they can see. If the metric is poorly chosen, the optimization is meaningless.

**Detection signal.** Benchmark improvements not accompanied by cheap-enemy comparison. A new metric that has no corresponding cheap baseline. Results that improve monotonically with complexity without a floor check.

**Mitigation.** `make bench-cheap-enemies`, `make bench-charge-matched`, `make bench-leakage`. Every advanced scorer must beat ALL declared cheap enemies before earning ranking authority. See `cheap_enemy_comparison.py`.

---

### FM-04: Safety weakening by omission

**What it is.** An agent removes a caveat, shortens a warning, or quietly increases a threshold without realizing the safety implication.

**Why it happens.** Agents prioritize coherence and concision. A long, hedged warning is "worse writing" than a short, confident statement. An agent optimizing for readability strips the very language that prevents overclaiming.

**Detection signal.** Diffs that shorten `known_failure_modes` lists. Diffs that remove "dry-lab only" or "not validated" qualifiers. Threshold changes that lower rejection rates without explanation.

**Mitigation.** Negative results, caveats, and failure modes are load-bearing. Do not delete them. The CLAUDE.md disconfirming pass explicitly checks: "Did any wording get stronger, any caveat get shorter, any negative result get quieter?" If yes, that is the finding.

---

### FM-05: Evidence certificate confusion

**What it is.** An agent issues or modifies an evidence certificate in a way that implies stronger biological support than the dry-lab data provides.

**Why it happens.** The certificate schema has many fields. An agent that does not understand the `proof_ladder_level` semantics may assign a level that implies assay confirmation when only computational evidence exists.

**Detection signal.** Certificates with `proof_ladder_level` ≥ `expert_reviewed_assay_proposal` generated without wet-lab input. Certificates missing `dry_lab_only: true`. Certificates with `unsupported_claims` lists that are empty or missing.

**Mitigation.** `dry_lab_only: true` must be set for all agent-generated certificates. `proof_ladder_level` must not exceed `multi_signal_candidate_evidence` for dry-lab artifacts. See `certificate.py` and `PROOF_LADDER.md`.

---

### FM-06: Calibration self-service

**What it is.** An agent proposes or implements a recalibration that benefits the current selection strategy without adversarial scrutiny.

**Why it happens.** Calibration updates feel like improvements. An agent that generates both the selection candidates and the calibration proposal has a structural conflict of interest — the new calibration will tend to favor the same patterns as the selection.

**Detection signal.** A recalibration proposed in the same loop as a candidate selection. Calibration changes that raise scores for the same sequences that were just selected. Calibration with no declared disconfirming test.

**Mitigation.** Calibration policy changes require human review. The stop rule in CLAUDE.md is explicit: "Stop and request human review if a change touches calibration policy." Agents may prepare recalibration proposals but must not apply them without human sign-off.

---

### FM-07: Hidden dependency introduction

**What it is.** An agent adds a new module, library, or external service without declaring the dependency or testing its absence.

**Why it happens.** Agents solve the problem in front of them. If a library would make the code cleaner, they add it. They do not always model the cost of adding a dependency for others.

**Detection signal.** Imports of packages not in `pyproject.toml` or `requirements*.txt`. Code that reaches network endpoints without a documented fallback. CI failures on fresh installs.

**Mitigation.** `make doctor` and `make agent-check` catch missing dependencies. Any new import must be accompanied by a `pyproject.toml` update. Network-dependent code must have a fail-closed fallback.

---

### FM-08: Novelty over-attribution

**What it is.** An agent reports high novelty scores as evidence of discovery without checking whether the query sequence is simply similar to a training data artifact rather than genuinely novel relative to known AMPs.

**Why it happens.** Novelty scores are easy to produce and hard to verify. An agent has no ground truth for whether something is genuinely novel.

**Detection signal.** Novelty claims not accompanied by similarity-neighbor reports. High novelty scores for sequences with high similarity to known positives. Novelty claims in PR descriptions without reference to a similarity check.

**Mitigation.** `similarity_neighbor_report.py` (C4) explicitly detects the novelty shortcut. Any high-novelty claim must be paired with a similarity report showing the nearest-neighbor distance.

---

### FM-09: Unsafe parallelism

**What it is.** An agent spawns multiple sub-agents writing to the same branch, schema file, or test file simultaneously, creating merge conflicts or corrupted state.

**Why it happens.** Parallelism feels efficient. Agents do not always track shared mutable resources.

**Detection signal.** Merge conflicts on test count regression files. Duplicate commit messages. Branch states that contain changes from multiple unrelated tasks.

**Mitigation.** One agent at a time per repo. The master loop rule is explicit: "spawn 1 opencode agent at a time." Clean up stale agent processes before dispatching a new one. Check `ps aux | grep opencode` before dispatch.

---

### FM-10: Stop condition ignored

**What it is.** An agent encounters a stop condition (safety policy, release policy, threshold change, public claim) and continues rather than halting and leaving a decision-log draft.

**Why it happens.** Stop conditions interrupt task completion. Agents optimize for task completion. The signal to stop is treated as an obstacle rather than a boundary.

**Detection signal.** PRs that touch release status, benchmark thresholds, calibration policy, or public scientific claims without a human reviewer noted. Decision logs missing for changes that should have triggered a stop.

**Mitigation.** The stop rule in CLAUDE.md is not advisory. When a stop condition fires, the correct output is a decision-log draft (see `decision_logs/INDEX.md`), not a PR. A stopped loop that leaves a clear handoff is more valuable than a merged PR that skipped a required review.

---

## Using this document

**For agents:** Read this list before every PR. Run the disconfirming pass from CLAUDE.md. If your change activates any signal in this list, stop and report.

**For reviewers:** Use this list as a review checklist. PR descriptions that explicitly name which failure modes were checked are more trustworthy than those that do not.

**For maintainers:** Update this document when new failure modes are observed in practice. A failure mode that happened once will happen again. A documented failure mode can be caught.
