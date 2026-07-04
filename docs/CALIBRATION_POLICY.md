# Recalibration Policy

> **Purpose:** Define the pre-registered, human-authored policy that gates
> any pipeline recalibration in OpenAMP Foundry. This document explains the
> policy; the machine-readable contract is `configs/recalibration_policy.yaml`.
>
> **Status:** v0.5.20 — ratified alongside the recalibration-gate CLI.

---

## Why this exists

Calibration intake (`openamp-foundry calibration-intake`, v0.5.19) joins
computational predictions with validated lab results and produces a
per-candidate report. It is intentionally **descriptive only**: it does
NOT trigger any weight update, scoring change, or selection rule
modification.

The next step in the wet-lab compression roadmap is to **act on** those
intake reports when the evidence is strong enough — and ONLY then. The
most dangerous failure mode is silent recalibration: an agent sees real
wet-lab data, decides the scorer "needs improvement," and rewrites
weights to fit. That is exactly the cherry-picking the project exists
to prevent.

This policy is the formal gate against silent recalibration. It
encodes:

- **minimum conditions** — what a cohort must look like before any
  recalibration is even considered (cohort size, controls, no orphans,
  confirmed actives and inactives);
- **prohibited actions** — permanent safety floors that no recalibration
  may relax (toxicity, hemolysis, novelty, pathogen enhancement, success
  redefinition);
- **rate limits** — how much weight can change per event and how often
  recalibration may occur;
- **required reviewer artefacts** — what humans must produce for a
  recalibration to be considered scientifically valid.

The policy is **machine-readable** (`configs/recalibration_policy.yaml`)
and **machine-enforced** (`openamp_foundry.calibration.policy` +
`openamp_foundry.calibration.recalibration_gate`). The CLI
`openamp-foundry recalibration-gate` evaluates an intake report against
the policy and emits a binary verdict plus a list of reasons.

---

## What the gate actually does

```bash
# 1. Generate an intake report from a pilot panel + lab results dir
make lab-result-intake PANEL=... RESULTS_DIR=...
# 2. Evaluate the recalibration gate against that report + the policy
make recalibration-gate INTAKE=outputs/calibration_intake.json
```

The gate:

1. Loads and validates `configs/recalibration_policy.yaml`. If a
   minimum_condition rule is missing its `locked_changes` entry, OR
   any canonical prohibited action is removed, the policy itself is
   rejected at load time.
2. Loads the intake report produced by `calibration-intake`.
3. Evaluates every `minimum_conditions` rule against the report. If
   ANY rule fails, the verdict is `may_recalibrate=false`.
4. Audits every `prohibited_actions` entry (informational only;
   surfaced in the verdict so reviewers see the floors).
5. Evaluates every `rate_limits` entry. When inputs are missing,
   status is `unknown`; when thresholds are violated, status is
   `exceeded` (and the verdict lists it as a reason).
6. Checks whether each `required_reviewer_artefacts` file exists on
   disk. Missing artefacts are surfaced but do not by themselves
   block the gate; the human review is the final step.

Exit code:

- `0` when `may_recalibrate=true`
- `3` when `may_recalibrate=false`
- `2` when an input is missing or malformed

---

## The minimum conditions

| Rule                          | Default | Purpose                                              |
|-------------------------------|---------|------------------------------------------------------|
| `MIN_COHORT_SIZE`             | 5       | Anti-cherry-picking floor for cohort size.            |
| `MIN_POSITIVES_IN_COHORT`     | 2       | At least two confirmed active hits.                   |
| `MIN_NEGATIVES_IN_COHORT`     | 2       | At least two confirmed inactive results.              |
| `POSITIVE_CONTROLS_ALL_PASS`  | true    | No failed positive controls allowed.                  |
| `NEGATIVE_CONTROLS_ALL_PASS`  | true    | No failed negative controls allowed.                  |
| `NO_ORPHAN_LAB_RESULTS`       | 0       | All lab results must match a panel candidate.         |
| `COHORT_METRICS_AVAILABLE`    | false   | Cohort metrics must not be flagged insufficient_data. |

Every rule is also listed in `locked_changes` in the policy YAML.
Removing or relaxing a rule requires bumping `policy_version` AND
writing a dated decision log entry that explains why.

---

## The prohibited actions (permanent floor)

These rules CANNOT be relaxed by any future policy edit. They duplicate
the non-negotiable safety floors already encoded in `AGENTS.md` and
`MISSION.md`.

| ID                                  | Why it is permanent                                  |
|-------------------------------------|------------------------------------------------------|
| `NO_TOXICITY_RELAXATION`            | AGENTS.md forbids activity-only optimization.       |
| `NO_HEMOLYSIS_RELAXATION`           | MISSION.md requires dual-use review.                |
| `NO_NOVELTY_RELAXATION`             | AGENTS.md identifies rediscovering AMPs as a threat.|
| `NO_DANGEROUS_PATHGEN_OPTIMIZATION` | AGENTS.md forbids dangerous operational content.    |
| `NO_POST_HOC_SUCCESS_REDEFINITION`  | Anti-cherry-picking; success must be fixed in advance.|

A policy file that omits any of these is rejected at load time. To
remove one entirely would require deleting the entire policy file and
starting from scratch — which is itself auditable in git history.

---

## Rate limits

| Rule                       | Default | Purpose                                       |
|----------------------------|---------|-----------------------------------------------|
| `WEIGHT_CHANGE_L1_BUDGET`  | 0.10    | Maximum L1 weight change per event.           |
| `COOLDOWN_DAYS`            | 14      | Minimum days between consecutive recalibrations. |

These are checked when the corresponding CLI inputs are supplied
(`--weight-l1-distance` and `--previous-recalibration-at`). Without
inputs, the status is `unknown` and the gate still answers the binary
question — but the verdict surfaces that the rate limit was not
evaluable.

---

## Required reviewer artefacts

| Artefact              | Path                                    | Purpose                            |
|-----------------------|-----------------------------------------|------------------------------------|
| `INTAKE_REPORT_JSON`  | `outputs/calibration_intake.json`       | Machine-readable intake report.    |
| `INTAKE_REPORT_MARKDOWN` | `outputs/calibration_intake.md`       | Human-readable intake report.      |
| `DECISION_LOG_ENTRY`  | `docs/DECISION_LOG_<YYYY-MM-DD>.md`     | Human-authored rationale + proposal.|

These are surfaced in the verdict and counted as `reasons` when missing,
but they do not by themselves block the gate. The human review IS the
final step.

---

## What this policy is NOT

- **Not a recalibrator.** The gate does not move weights or change
  scoring. It only emits a verdict.
- **Not a replacement for human review.** A `may_recalibrate=true`
  verdict is a *permission*, not a *command*. The decision to actually
  apply a weight change still belongs to a human reviewer with a
  documented decision log entry.
- **Not a static barrier.** A future maintainer may relax the cohort
  size threshold from 5 to 7 if the evidence justifies it. They MUST
  bump `policy_version` and write a decision log entry first. The
  validator surfaces missing `locked_changes` entries as load errors.
- **Not a substitute for benchmark honesty.** The gate evaluates
  *cohort evidence*, not pipeline calibration health. Benchmark
  regressions are caught by `make validate-scoring` and the triage
  benchmark, not by this policy.

---

## How to update the policy

If real wet-lab data justifies a policy change:

1. Open `configs/recalibration_policy.yaml`.
2. Bump `policy_version` (integer; never decrement).
3. Update `locked_at` to today's ISO date.
4. Update `human_reviewer` to identify the reviewer.
5. Make the rule changes.
6. If a rule is being RELAXED, add a `locked_changes` entry with the
   new `locked_at` date and the reason.
7. If a rule is being REMOVED, add a decision log entry
   (`docs/DECISION_LOG_<date>.md`) explaining why. The validator will
   reject the file until the removal is recorded.
8. If a canonical prohibited action is being removed entirely, STOP.
   That change is not allowed.

The policy validator (`openamp_foundry.calibration.policy`) enforces
steps 5–7 mechanically. The CI gate
(`tests/test_recalibration_gate.py::test_canonical_prohibited_actions_match_policy`)
enforces the canonical prohibited-action list.

---

## How this fits the wet-lab compression roadmap

| Roadmap step                | Status        | Where it lives                              |
|-----------------------------|---------------|---------------------------------------------|
| Lab-result schema           | Done (v0.5.18)| `schemas/lab_result.schema.json`            |
| Lab-result intake report    | Done (v0.5.19)| `openamp_foundry.calibration.intake`        |
| **Recalibration policy**    | **Done (v0.5.20)** | `configs/recalibration_policy.yaml` + `openamp_foundry.calibration.policy` + `openamp_foundry.calibration.recalibration_gate` |
| Recalibration *engine*      | Pending       | Future loop, after real lab data arrives     |
| Active-learning selection   | Pending       | Future loop, depends on recalibration engine |

The recalibration policy is the **gate that protects** the
recalibration engine. Building the engine without the gate would be
silent cherry-picking. Building the gate now — before real data
arrives — is the honest sequence.

---

## Quick command reference

```bash
# Show policy summary (no evaluation needed)
cat configs/recalibration_policy.yaml | head -40

# Run the synthetic example end-to-end
make lab-result-intake-example
make recalibration-gate-example
# Expect exit code 3 (FAIL) because the synthetic cohort is too small
# and one positive control failed.

# Evaluate a real intake report
make recalibration-gate \
  INTAKE=outputs/calibration_intake.json \
  DATE=2026-08-15 \
  PREV=2026-07-01 \
  L1=0.05

# Run the gate in tests
pytest tests/test_recalibration_gate.py -v
```
