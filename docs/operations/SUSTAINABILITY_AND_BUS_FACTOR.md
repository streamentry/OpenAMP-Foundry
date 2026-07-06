# Sustainability and Bus Factor

## Purpose

This document defines how OpenAMP Foundry should remain useful if maintainers change, agents rotate, contributors leave, or strategic memory fades.

Infrastructure must outlive its original author.

## Prime rule

**No critical project knowledge should live only in one person’s head.**

## Sustainability surfaces

| Surface | Sustainability need |
|---|---|
| Mission | Clear enough for new maintainers to preserve scope. |
| Safety | Enforced by docs, templates, and review gates. |
| Claims | Mapped to proof ladder and review checklist. |
| Benchmarks | Governed by cards, thresholds, and source-of-truth metrics. |
| Data | Governed by dataset cards and license records. |
| Models | Governed by model cards and release status. |
| Agents | Governed by operating contract and issue labels. |
| Releases | Governed by checklist and decision records. |
| Roadmap | Expressed as PR-sized tasks. |

## Bus-factor risks

### Risk 1 — Strategic memory is private

Mitigation:

- `VISION.md`;
- `GOAL.md`;
- `docs/PROJECT_INDEX.md`;
- `docs/NEXT_100_PR_MAP.md`;
- `GOVERNANCE.md`;
- decision records.

### Risk 2 — Safety decisions depend on intuition

Mitigation:

- safety policy;
- model release policy;
- responsible use policy;
- safety review templates;
- safety-doc audit.

### Risk 3 — Benchmarks become cargo cult

Mitigation:

- benchmark governance;
- benchmark cards;
- metrics source-of-truth;
- cheap-baseline policy.

### Risk 4 — Agents create unreviewable churn

Mitigation:

- agent operating contract;
- human-agent collaboration model;
- agent-safe issue templates;
- reviewer onboarding.

## Maintainer handoff checklist

A new maintainer should be able to answer:

1. What is the project trying to become?
2. What must it never claim without evidence?
3. What changes require safety review?
4. What benchmarks are source-of-truth?
5. What artifacts are stable interfaces?
6. What docs must be updated when behavior changes?
7. What issues are safe for agents?
8. What is the current strategic bottleneck?
9. What decision records matter most?
10. What release checklist must be followed?

## Succession-ready files

The repo is succession-ready when these are current:

- `README.md`;
- `GOVERNANCE.md`;
- `SAFETY.md`;
- `MODEL_RELEASE_POLICY.md`;
- `docs/PROJECT_INDEX.md`;
- `docs/TRUST_CENTER.md`;
- `docs/METRICS_CURRENT.md`;
- `docs/NEXT_100_PR_MAP.md`;
- `docs/RELEASE_CHECKLIST.md`;
- `docs/RISK_REGISTER.md`.

## Documentation debt policy

Documentation debt becomes operational debt when:

- a contributor cannot tell which doc is source-of-truth;
- agents act on stale instructions;
- release status is unclear;
- benchmark meaning is unclear;
- public claims drift from evidence;
- safety boundaries require private explanation.

When this happens, prioritize documentation repair over new features.

## Final standard

OpenAMP should become easier to maintain as it grows.

If growth makes the project depend more on private memory, the infrastructure thesis is failing.
