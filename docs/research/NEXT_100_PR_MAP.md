# Next 100 PR Map

## Purpose

This document translates the OpenAMP vision into a concrete sequence of small, reviewable PRs.

The goal is to make the repo the obvious place where humans and agents can do useful work without needing private maintainer context.

Each PR should be narrow enough to review and strong enough to compound.

## Execution principle

```text
one PR = one bottleneck removed + evidence + docs + safety check
```

Do not use this map as permission for broad autonomous changes.

Safety-sensitive, wet-lab-facing, candidate-release, benchmark-threshold, calibration-policy, or claim-strengthening work requires human review.

## Phase A — First-run excellence

Make the repo easier to run, understand, and verify.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| A1 | Add a `make doctor` command that checks Python version, package install, expected folders, and key optional tools. | New users fail less. | B |
| A2 | Add `openamp-foundry doctor` CLI equivalent. | Agents can self-diagnose environment issues. | B |
| A3 | Generate a first-run report after `make demo`. | New users understand outputs faster. | B |
| A4 | Add a `docs/getting-started/FIRST_RUN_WALKTHROUGH.md` with expected outputs and claim boundaries. | Converts demo into onboarding. | A |
| A5 | Add test that README quickstart commands stay valid. | Prevents entrypoint drift. | B |
| A6 | Add link-check CI for internal docs. | Prevents doc graph rot. | B |
| A7 | Add a `make docs-check` target. | Agents can verify doc-only PRs. | B |
| A8 | Add generated artifact examples with safe toy data. | Reviewers see what good output looks like. | B |
| A9 | Add `outputs/README.md` explaining generated outputs and ignored files. | Reduces confusion. | A |
| A10 | Add troubleshooting table for install/test failures. | Faster onboarding. | A |

## Phase B — Evidence certificate hardening

Make candidate evidence packages impossible to confuse with biological proof.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| B1 | Add certificate field for `proof_ladder_level`. | Claims become machine-checkable. | B |
| B2 | Add `unsupported_claims` field to certificates. | Prevents score-to-proof drift. | B |
| B3 | Add `baseline_caveat` field. | Forces cheap-explanation visibility. | B |
| B4 | Add `release_status` field. | Supports staged release. | C/D |
| B5 | Add certificate quality-tier validator. | External-review readiness becomes measurable. | B |
| B6 | Add human-readable certificate report. | Domain experts can inspect faster. | B |
| B7 | Add candidate rejection certificate support. | Failures become artifacts. | B |
| B8 | Link certificates to run manifest hashes. | Stronger reproducibility. | B |
| B9 | Add test that dry-lab certificates cannot include forbidden claims. | Claim discipline in CI. | B/C |
| B10 | Add external-review packet generator that bundles certificates. | Better partner review. | C/D |

## Phase C — Benchmark honesty expansion

Make OpenAMP the hardest repo to fool in AMP dry-lab selection.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| C1 | Create machine-readable benchmark cards. | Governance becomes enforceable. | B |
| C2 | Add benchmark-card schema. | Prevents incomplete benchmark docs. | B |
| C3 | Add charge-distribution report for every benchmark. | Shortcut visibility. | B/C |
| C4 | Add similarity-neighbor distribution report. | Novelty honesty. | B/C |
| C5 | Add `bench-length-matched` control. | Tests length shortcut. | C |
| C6 | Add `bench-charge-length-matched` control. | Stronger nontrivial signal test. | C |
| C7 | Add family-stratified precision@k. | Helps panel design. | C |
| C8 | Add benchmark-deprecation banner system. | Prevents stale benchmark authority. | B |
| C9 | Add command that compares all advanced scorers against declared cheap enemies. | Standardizes anti-hype. | C |
| C10 | Add benchmark governance CI that rejects missing benchmark cards for new benchmark scripts. | Prevents benchmark sprawl. | B/C |

## Phase D — Agent excellence

Make OpenAMP a gold-standard repo for safe agent contribution.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| D1 | Add `AGENT_TASKS.json` with machine-readable task categories and forbidden zones. | Agents can self-classify tasks. | B |
| D2 | Add agent-safe issue examples. | Better issue creation. | A |
| D3 | Add agent PR self-check script that scans for forbidden claim language. | Automated guardrails. | B |
| D4 | Add docs-only PR verifier. | Faster safe doc work. | B |
| D5 | Add `make agent-check` target combining doc links, claim scan, and safety phrase scan. | Agent-friendly verification. | B |
| D6 | Add agent stop-condition examples. | Reduces scope creep. | A |
| D7 | Add maintainer prompts for assigning agent-safe tasks. | Better human-agent coordination. | A |
| D8 | Add `docs/AGENT_FAILURE_MODES.md`. | Makes agent risks explicit. | A |
| D9 | Add CI warning for newly added top-level docs not in project index. | Prevents hidden docs. | B |
| D10 | Add structured agent contribution summary template. | Easier review. | B |

## Phase E — Safe external review infrastructure

Make qualified external review easier and safer.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| E1 | Add external review packet schema. | Packets become machine-checkable. | C/D |
| E2 | Add example external review packet using toy data. | Partners know what to expect. | C/D |
| E3 | Add reviewer questionnaire JSON schema. | Review feedback becomes structured. | B/C |
| E4 | Add safety-release decision schema. | Release review becomes auditable. | D |
| E5 | Add non-protocol pilot pre-registration schema. | Freezes selection logic. | C/D |
| E6 | Add packet generator CLI. | Reduces manual packaging errors. | C/D |
| E7 | Add packet validator CLI. | Review readiness becomes testable. | C/D |
| E8 | Add release-summary generator that strips restricted fields. | Safer public summaries. | D |
| E9 | Add domain-review outcome taxonomy. | Rejection becomes structured. | B/C |
| E10 | Add expert-review example with mock/toy candidates only. | Safe demonstration. | B/C |

## Phase F — Negative-result infrastructure

Make failure useful.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| F1 | Add negative-result entry schema hardening. | Failure records become useful. | B/C |
| F2 | Add negative-result archive validator. | Prevents incomplete records. | B |
| F3 | Add rejection reason entry schema (complete). | Enables analysis of failed candidates with controlled vocabulary of stages and reasons; feeds calibration loop with structured failure signal. | B |
| F4 | Add failed-candidate report generator. | Makes failed batches reviewable. | B/C |
| F5 | Add safe-publication filter for negative results. | Supports openness without unsafe release. | D |
| F6 | Add examples of non-informative vs informative negative results. | Better interpretation. | A |
| F7 | Add calibration link from negative-result entries to intake reports. | Closes learning loop. | C |
| F8 | Add benchmark for whether rejected candidates resemble known failure modes. | Improves rejection logic. | C |
| F9 | Add negative-result dashboard from toy data. | Shows value of failures. | B |
| F10 | Add policy that public claims must mention relevant negative results. | Prevents cherry-picking. | D |

## Phase G — Calibration and active-learning rigor

Make learning controlled rather than self-serving.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| G1 | Add machine-readable recalibration decision log examples. | Improves governance memory. | B |
| G2 | Add recalibration rejection examples. | Shows gate success by refusal. | B |
| G3 | Add `make calibration-audit`. | Checks intake/gate/engine/report consistency. | C |
| G4 | Add active-learning strategy comparison report. | Prevents one-selector bias. | C |
| G5 | Add batch-2 rationale report explaining exploit/explore/diversity roles. | Reviewers understand next batch. | C |
| G6 | Add calibration-overfit warning when cohort is too small. | Prevents false learning. | C |
| G7 | Add result-quality flag propagation into calibration engine. | Low-quality outcomes cannot drive updates. | C |
| G8 | Add policy that synthetic results cannot raise proof-ladder level. | Anti-overclaim. | B/C |
| G9 | Add calibration decision review checklist. | Human review stronger. | C/D |
| G10 | Add recalibration rollback plan. | Safer updates. | C |

## Phase H — Virtual assay discipline

Make simulation useful or harmless.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| H1 | Add simulation module registry. | Shows status and evidence level. | B |
| H2 | Add simulation-result schema. | Prevents undocumented proxy output. | B/C |
| H3 | Add per-module cheapest-baseline declaration. | Forces enemy comparison. | C |
| H4 | Add fail-closed adapter integration tests. | Avoids hidden external failures. | B/C |
| H5 | Add no-silent-network policy test for adapters. | Protects sequence privacy. | D |
| H6 | Add simulation uncertainty calibration report. | Makes uncertainty inspectable. | C |
| H7 | Add documentation that failed simulation stays useful as negative evidence. | Cultural standard. | A |
| H8 | Add `weighted` integration dry-run report, still blocked by gate. | Shows what would change without applying. | C |
| H9 | Add module deprecation mechanism for simulation theater. | Cleanup discipline. | B/C |
| H10 | Add external-simulator review checklist. | Safer ecosystem bridges. | D |

## Phase I — Interoperability and adoption

Make OpenAMP artifacts useful even without OpenAMP scoring.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| I1 | Add artifact versioning policy. | External users need stability. | B |
| I2 | Add candidate manifest schema. | Core interoperable artifact. | B/C |
| I3 | Add benchmark card schema. | External benchmarks easier. | B |
| I4 | Add evidence-certificate changelog. | Backward compatibility. | B |
| I5 | Add downstream project template. | External adoption. | B |
| I6 | Add adapter author guide. | Better ecosystem modules. | B/C |
| I7 | Add data license checker. | Avoids hidden legal risk. | B |
| I8 | Add artifact compatibility tests. | Prevents schema drift. | B |
| I9 | Add public-good contribution guide for institutions. | Funders know how to help. | A |
| I10 | Add adoption scorecard dashboard. | Measures real use, not stars. | B |

## Phase J — Governance and release maturity

Make success survivable.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| J1 | Add release checklist. | Safer releases. | B/D |
| J2 | Add governance decision log index. | Decisions discoverable. | B |
| J3 | Add model/candidate release request template. | Reviewable releases. | D |
| J4 | Add conflict-of-interest disclosure template. | Institutional trust. | B |
| J5 | Add maintainer rotation / bus-factor plan. | Project durability. | A/B |
| J6 | Add security policy for private vulnerability reporting. | Repo maturity. | B |
| J7 | Add citation and reuse guide. | Ecosystem clarity. | A |
| J8 | Add roadmap-to-issue sync checklist. | Keeps strategy actionable. | B |
| J9 | Add external advisory review process. | Credibility. | D |
| J10 | Add annual safety and benchmark review checklist. | Long-term trust. | D |

## Phase K — External Pilot Readiness

Build the evidence and accountability artifacts needed for credible external validation.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| K1 | Add candidate selection rationale schema. | Auditable selection decisions. | B |
| K2 | Add batch experiment priority ranker. | Rank candidates for next synthesis wave. | B |
| K3 | Add pilot package completeness checker. | All components present before submission. | B |
| K4 | Add post-experiment calibration intake schema. | Structured result-to-prediction comparison. | B/D |
| K5 | Add uncertainty quantification report schema (complete — Loop 123). | Honest prediction intervals for reviewers. | B |

## Phase L — Scientific Communication

Bridge the gap between evidence packages and published science.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| L1 | Add preprint evidence bundle schema (complete — Loop 124). | Ties K-phase artifacts into a submission-ready package. | B |
| L2 | Add reproducibility manifest schema (complete — Loop 125). | Captures exact versions, checksums, seeds for full reproduction. | B |
| L3 | Add candidate summary card schema (complete — Loop 126). | Publication-ready per-candidate structured summary. | B |
| L4 | Add multi-candidate comparison schema (complete — Loop 126b). | Structured comparison table for ≥2 candidates. | B |
| L5 | Add dataset release package checker (complete — Loop 127). | Validates open dataset releases meet data governance. | B/D |


## Phase M — Audit Trail Infrastructure

Make every pipeline decision traceable, independently verifiable, and resistant to post-hoc rationalization.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| M1 | Add pipeline decision audit entry schema (complete — Loop 128). | Records filter/threshold/rank decisions with rationale for external audit. | B |
| M2 | Add claim-to-evidence mapper schema (complete — Loop 129). | Maps each scientific claim to the artifact that supports it. | B |
| M3 | Add score decomposition report schema (complete — Loop 130). | Documents how composite scores are computed from components. | B |
| M4 | Add reviewer briefing package checker (complete — Loop 131). | One-stop summary that external reviewers need before auditing. | B |
| M5 | Add audit chain completeness checker (complete — Loop 132). | Validates the evidence chain has no gaps from sequences to submission. Completes Phase M. | B/D |

## Phase N — Pre-registration & Baseline Honesty

Make experiment predictions falsifiable before results are observed. Guard against HARKing and post-hoc rationalization.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| N1 | Add pre-registration form schema (complete — Loop 133). | Records what will be tested and how before experiments run. | B |
| N2 | Add hypothesis outcome record schema (complete — Loop 134). | Documents whether pre-registered hypotheses were confirmed or refuted. | B/D |
| N3 | Add baseline comparison manifest schema (complete — Loop 135). | Machine-verifiable proof the model beats cheap baselines. | B |
| N4 | Add negative result record schema (complete — Loop 136). | Ensures failed experiments are documented, not discarded. | B | | Ensures failed experiments are documented, not discarded. | B |
| N5 | Add experiment priority justification schema (complete — Loop 137). | Documents why this batch was selected over alternatives. Completes Phase N. | B |

## Phase O — Calibration Quality Assurance

Track how well predictions match experimental outcomes over time. Detect drift, overconfidence, and systematic bias before they compound.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| O1 | Add calibration performance summary schema (complete — Loop 138). | Aggregates prediction accuracy metrics across batches with known outcomes. | B/D |
| O2 | Add prediction drift monitor schema (complete — Loop 139). | Detects when pipeline predictions are systematically shifting. | B/D |
| O3 | Add calibration improvement record schema. | Documents what was changed to improve calibration and by how much. | B/D |
| O4 | Add cross-batch performance aggregator schema (complete — Loop 140). | Aggregates results across batches for trend analysis. | B/D |
| [x] O5 | Add calibration readiness gate schema. | Validates calibration quality is sufficient before releasing the next batch. | B/D |

## Phase P — Calibration-to-Selection Bridge

Close the loop from Phase O calibration quality assurance back to candidate
selection.  A batch can only be proposed when the calibration gate passes,
preventing the pipeline from selecting candidates under poor calibration.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| P1 | Add batch selection proposal schema (complete). | Enforces calibration gate must pass before proposing a next batch; documents exploitation/exploration strategy. | B/D |
| P2 | Add recalibration refusal record schema (complete). | Documents when recalibration was correctly rejected; prevents spurious recalibrations and creates audit trail. | B/D |
| P3 | Add batch outcome summary schema (complete). | Closes the BSP→lab→outcomes feedback loop; enforces synthetic/real boundary at the batch level. | B/D |
| P4 | Add pilot batch safety clearance schema (complete). | Safety gate before wet-lab synthesis: all 4 screens required, high-risk batches cannot be cleared. | B/D |
| P5 | Add calibration cycle summary schema (complete). | Index record for one complete BSP→PSC→BOS→CPS→CBA→CRG cycle; crg_id_previous must differ from crg_id_next. | B/D |

## Phase Q — External Pilot Package Readiness

Package and validate the evidence chain for external lab partners. A complete
pilot package references pre-registration, baseline comparisons, calibration
cycles, safety clearance, and candidate batch proposal — in one verifiable
bundle.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| Q1 | Add pilot evidence package schema (complete). | External export artifact: bundles CCS+BSP+PSC+PRE+BCM references, enforces completeness and safety clearance before external sharing. | B/D |
| Q2 | Add pre-registration entry schema (complete). | Locks hypothesis, endpoint, and candidate list before wet-lab begins; prevents HARKing; referenced by PEP as pre_registration_id. | B/D |
| Q3 | Add external sharing clearance schema (complete). | Auditable release gate: records who received a PEP, when, with what dry-lab caveat confirmation; no PEP leaves the foundry without an ESC record. | B/D |

## Prioritization rule

When choosing between tasks, prefer the one that:

1. prevents unsafe or unsupported claims;
2. improves external reviewability;
3. strengthens benchmark honesty;
4. reduces agent/human coordination cost;
5. improves reproducibility;
6. creates reusable artifacts;
7. moves toward a pre-registered, baseline-controlled external pilot.

## Stop conditions

Stop a PR or split it when:

- it crosses into wet-lab operational detail;
- it changes safety policy without review;
- it changes ranking and benchmarks at the same time without a clear plan;
- it strengthens claims without proof-ladder mapping;
- it publishes candidate details without release review;
- it creates broad refactor risk;
- it cannot be tested or reviewed.

## Final standard

The next 100 PRs should make OpenAMP less dependent on trust in any one person, model, lab, agent, or narrative.

That is how a repo becomes infrastructure.
