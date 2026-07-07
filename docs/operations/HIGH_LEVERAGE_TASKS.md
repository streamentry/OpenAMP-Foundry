# High-Leverage Task Map

## Purpose

This document helps humans and agents choose work that moves OpenAMP Foundry toward becoming the default open infrastructure for trustworthy antimicrobial peptide experiment selection.

The goal is not more activity.

The goal is more compounding.

## Task selection rule

Choose the task that most increases one of these:

1. Scientific truthfulness.
2. Safety.
3. Reproducibility.
4. Decision quality.
5. External usefulness.
6. Agent/human continuation speed.

Avoid tasks that only make the repo look more advanced.

## Current strategic bottleneck

The repo already has a strong dry-lab foundation, calibration scaffolding, benchmark discipline, and safety framing.

The bottleneck is now external credibility:

```text
Can the system help choose real experiments better than cheap baselines?
```

Tasks should increasingly point toward:

- external review;
- fair baseline comparison;
- pre-registered pilot packages;
- result intake;
- negative-result preservation;
- calibration that improves the next batch.

## Tier 0 — Safety and claim integrity

These tasks outrank everything else.

### Task: Claim audit

Review README, docs, reports, and generated text for unsupported language.

Upgrade: stronger claim discipline.

Verification:

- no Level 6+ language for dry-lab artifacts;
- claims map to [`PROOF_LADDER.md`](../evidence/PROOF_LADDER.md);
- forbidden phrases removed or qualified.

### Task: Candidate release audit

Check whether any outputs, examples, or docs could be interpreted as unscreened high-risk candidate publication.

Upgrade: safer release posture.

Verification:

- examples remain toy/demo where intended;
- release boundaries are explicit;
- unsafe publication paths are blocked or documented.

### Task: Safety checklist expansion

Improve PR, release, or model-adapter checklists.

Upgrade: safer human and agent contributions.

Verification:

- checklist catches a concrete failure mode;
- docs link to relevant safety policy;
- no ambiguity around human review.

## Tier 1 — Reproducibility and auditability

### Task: Run manifest hardening

Ensure major outputs include or reference:

- commit hash;
- config path/hash;
- input path/hash;
- random seed;
- package version;
- generation command;
- timestamp where appropriate.

Upgrade: easier external audit.

Verification:

- schema or tests enforce required fields;
- generated report displays them.

### Task: Evidence certificate readability

Improve evidence certificates so humans can understand why a candidate was selected or rejected.

Upgrade: better lab/expert review.

Verification:

- certificate still validates;
- report includes limitations and failure modes;
- reviewer can reconstruct selection logic.

### Task: Determinism check expansion

Add tests that rerun pipeline steps and compare outputs.

Upgrade: lower reproducibility risk.

Verification:

- test fails if nondeterminism enters an output path;
- seed/config behavior is documented.

## Tier 2 — Benchmark honesty

### Task: Charge-matched challenge expansion

Create stronger controls that prevent activity scoring from winning merely by preferring cationic sequences.

Upgrade: harder-to-fool benchmark.

Verification:

- charge distribution between positives and negatives is reported;
- pipeline performance is compared against charge-only baseline;
- caveats are added to `METRICS_CURRENT.md`.

### Task: Similarity-neighbor challenge

Test whether top candidates are mostly near-neighbors of known AMPs.

Upgrade: stronger novelty claims.

Verification:

- similarity distribution reported;
- near-duplicate threshold justified;
- novelty claims downgraded where needed.

### Task: Family-blindness challenge

Expand per-family benchmark analysis so weak AMP classes are visible and not excluded by ranker bias.

Upgrade: better experimental panel design.

Verification:

- per-family metrics reported;
- panel selection compensates for weak classes;
- docs state this is not evidence that weak classes are better.

### Task: Cheap-baseline harness

Make it easy for any new scorer or simulation module to declare and run its cheapest meaningful baseline.

Upgrade: permanent anti-hype infrastructure.

Verification:

- new scorer tests fail without baseline comparison;
- report shows delta vs baseline.

## Tier 3 — Human and lab usefulness

### Task: External review packet generator

Generate a complete review packet from candidate outputs.

Packet should include:

- candidate manifest;
- evidence certificates;
- novelty summary;
- safety-risk summary;
- synthesis summary;
- diversity rationale;
- benchmark caveats;
- unsupported-claim warning;
- reviewer questionnaire.

Upgrade: better expert collaboration.

Verification:

- generated packet is deterministic;
- schema validates included artifacts;
- docs explain how to review without private context.

### Task: Reviewer questionnaire hardening

Improve expert-review forms so reviewers can reject candidates for concrete reasons.

Upgrade: better human decision-making.

Verification:

- questionnaire covers novelty, controls, safety, synthesis, and claim scope;
- answer format can be parsed or summarized.

### Task: Pre-registration template

Create a template for freezing candidate selection, baselines, controls, and success/failure criteria before any pilot.

Upgrade: lower cherry-picking risk.

Verification:

- template includes baseline panels;
- success criteria cannot be silently changed;
- docs link to proof ladder.

## Tier 4 — Calibration and active learning

### Task: Batch-2 explanation report

When selecting a second batch, generate a report explaining which candidates are likely winners and which are uncertainty probes.

Upgrade: clearer learning logic.

Verification:

- each selected candidate has a reason category;
- safety gates are visible;
- diversity and uncertainty tradeoff is reported.

### Task: Synthetic-to-real boundary warning

Ensure every synthetic lab-result path clearly labels synthetic evidence and prevents accidental interpretation as real validation.

Upgrade: anti-overclaim protection.

Verification:

- generated files carry synthetic labels;
- reports state synthetic data cannot support biological claims;
- tests enforce labels.

### Task: Recalibration refusal examples

Add example artifacts where recalibration is correctly rejected.

Upgrade: trust in the gate.

Verification:

- gate exits with rejection code;
- report explains why;
- docs say rejection is success when evidence is weak.

## Tier 5 — Ecosystem and interoperability

### Task: Adapter registry

Create a documented registry of external predictor and simulation adapters, including status and evidence level.

Upgrade: easier extension without false trust.

Verification:

- each adapter has scope, version, inputs, outputs, limitations, and baseline result;
- unsupported adapters cannot affect ranking.

### Task: Artifact compatibility policy

Define which schemas are stable, experimental, or deprecated.

Upgrade: external adoption.

Verification:

- schema versions documented;
- breaking-change policy exists;
- deprecated artifacts remain readable where practical.

### Task: Downstream project template

Create a minimal template for external groups that want to use OpenAMP evidence certificates or result schemas.

Upgrade: ecosystem growth.

Verification:

- template runs without private data;
- safety docs included;
- claim ladder included.

## Tier 6 — Scientific frontier work

These tasks are valuable only if they remain benchmarked and claim-limited.

### Task: Better selectivity predictor

Add or adapt a predictor for bacterial-vs-mammalian selectivity.

Required evidence:

- comparison against cheap selectivity proxies;
- within-AMP safety benchmark;
- uncertainty reporting;
- fail-closed behavior.

### Task: Stability/protease-risk proxy

Add a stability-related signal.

Required evidence:

- clear scope;
- benchmark or literature-supported limitation;
- no claim of in vivo stability;
- baseline comparison.

### Task: Embedding-based diversity or novelty module

Add representation-aware diversity or novelty scoring.

Required evidence:

- comparison against sequence-similarity baseline;
- family-stratified behavior;
- failure modes;
- no silent model downloads.

### Task: Active-learning policy comparison

Compare multiple batch-selection strategies.

Required evidence:

- random baseline;
- top-k exploitation baseline;
- uncertainty-only baseline;
- diversity-only baseline;
- safety-adjusted yield metric;
- pre-registered evaluation.

## Task difficulty labels

Use these labels in issues or planning docs.

| Label | Meaning |
|---|---|
| `good-first-task` | Small, safe, clear verification path. |
| `agent-safe` | Suitable for autonomous or semi-autonomous agents. |
| `needs-domain-review` | Requires microbiology, peptide, toxicology, or assay expertise. |
| `needs-safety-review` | Could affect release, safety, claims, or misuse risk. |
| `benchmark-critical` | Affects evidence or regression gates. |
| `wet-lab-facing` | Changes artifacts that a lab or expert may review. |
| `do-not-automerge` | Human review mandatory. |

## Kill criteria for tasks

Stop or downgrade a task when:

- it cannot be tested;
- it requires unsafe content;
- it strengthens claims without evidence;
- it fails against a cheap baseline;
- it introduces hidden data or nondeterminism;
- it makes external review harder;
- it creates maintenance burden without strategic leverage.

## What to do after finishing a task

After any meaningful task:

1. Update the source-of-truth doc if metrics, behavior, or claims changed.
2. Add tests or explain why the change is docs-only.
3. Record limitations.
4. Link related docs.
5. Make the next task obvious.

A good contribution should leave a trail.

## The highest-leverage future milestone

The single highest-leverage milestone is a pre-registered, safety-reviewed, baseline-controlled external pilot package.

Not because it will necessarily succeed.

Because it will reveal what the repo is actually worth under real experimental pressure.

Every task that makes that milestone more honest, safer, cheaper, or easier to review is high leverage.
