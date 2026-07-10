# Agent Contribution Summary Template

Use this template when an agent creates a PR. Copy it into the PR body.
Fill every section — omitting a section is a signal that the check was not performed.

---

## Task

<!-- One sentence: what bottleneck was this PR assigned to remove? -->

**Assigned bottleneck:**

**Evidence the bottleneck existed:**

**Smallest change that removes it:**

---

## Change summary

<!-- What files changed and why. One line per file. -->

| File | Change type | Why |
|------|-------------|-----|
| | | |

---

## Failure mode self-check

<!-- Check each row against docs/AGENT_FAILURE_MODES.md before opening PR. -->

| Failure mode | Checked? | Notes |
|---|---|---|
| FM-01 Claim escalation | ☐ Yes / ☐ No | |
| FM-02 Silent scope creep | ☐ Yes / ☐ No | |
| FM-03 Benchmark optimization theater | ☐ Yes / ☐ No | |
| FM-04 Safety weakening by omission | ☐ Yes / ☐ No | |
| FM-05 Evidence certificate confusion | ☐ Yes / ☐ No | |
| FM-06 Calibration self-service | ☐ Yes / ☐ No | |
| FM-07 Hidden dependency introduction | ☐ Yes / ☐ No | |
| FM-08 Novelty over-attribution | ☐ Yes / ☐ No | |
| FM-09 Unsafe parallelism | ☐ Yes / ☐ No | |
| FM-10 Stop condition ignored | ☐ Yes / ☐ No | |

---

## Disconfirming pass

<!-- Try to break your own change before shipping. Fill in each row. -->

| Check | Result |
|---|---|
| Cheapest explanation: could a one-line heuristic produce this result? | |
| Leakage: did improvement come from the method or the split? | |
| Silent scope creep: does the diff touch only the named bottleneck? | |
| Hidden certainty: did any wording get stronger or any caveat get shorter? | |
| Uninformative uncertainty: does the module report similar confidence for good and absurd inputs? | |

---

## Automated checks

<!-- Run these before opening the PR. Fill in the result. -->

| Check | Command | Result |
|---|---|---|
| Claim language | `make claim-check` | ☐ Pass / ☐ Fail |
| Doc links | `make doc-links-check` | ☐ Pass / ☐ Fail |
| Benchmark deprecation | `make bench-deprecation-check` | ☐ Pass / ☐ Fail |
| Full agent check | `make agent-check` | ☐ Pass / ☐ Fail |
| Environment | `make doctor` | ☐ Pass / ☐ Fail |

---

## Stop conditions

<!-- Mark any that apply. If any are marked, STOP — do not open a PR. Instead, write a decision-log draft. -->

- ☐ Change touches safety policy
- ☐ Change touches release policy or release status
- ☐ Change touches candidate release
- ☐ Change touches model release
- ☐ Change touches non-toy data
- ☐ Change touches external-facing artifacts
- ☐ Change touches benchmark thresholds
- ☐ Change touches calibration policy
- ☐ Change touches public scientific claims

**If any box above is checked:** Stop. Write a decision-log draft under `decision_logs/` and request human review. Do not open a PR.

---

## Test coverage

<!-- For code PRs only. For docs-only PRs, mark N/A. -->

| Item | Value |
|---|---|
| New tests added | |
| BASELINE before | |
| BASELINE after | |
| Test command run | `pytest` |
| Result | ☐ Pass / ☐ Fail / ☐ N/A |

---

## Proof ladder level

<!-- For PRs that add or modify evidence artifacts. For infra/docs PRs, mark N/A. -->

| Item | Value |
|---|---|
| Proof ladder level of output | |
| `dry_lab_only` enforced | ☐ Yes / ☐ No / ☐ N/A |
| `unsupported_claims` present | ☐ Yes / ☐ No / ☐ N/A |

---

## One-sentence verdict

<!-- Complete this sentence: \"This PR [does X] and [moves OpenAMP closer to / does not affect] the mission by [Y].\" -->

> This PR _______________
