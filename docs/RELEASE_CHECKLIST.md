# Release Checklist

## Purpose

This checklist defines what must be true before OpenAMP Foundry publishes a release, public artifact, candidate package, benchmark result, or external-facing claim.

A release is a trust event.

## Prime rule

**A release must state not only what improved, but what remains unproven.**

## Release types

| Type | Examples | Review bar |
|---|---|---|
| Patch release | bug fixes, docs, minor tests | Standard maintainer review. |
| Infrastructure release | schemas, CLIs, reports, validators | Tests, docs, compatibility note. |
| Scientific behavior release | scorers, ranking, benchmarks, calibration | Benchmark and baseline review. |
| Safety-sensitive release | model artifacts, candidate panels, external handoffs | Safety review mandatory. |
| Public claim release | blog, abstract, paper, announcement | Proof-ladder review mandatory. |

## Pre-release checklist

### 1. Scope

- [ ] Release type identified.
- [ ] Change log written.
- [ ] Breaking changes identified.
- [ ] Experimental features labeled.
- [ ] Deprecated artifacts identified.

### 2. Tests and reproducibility

- [ ] `make test` or equivalent passes.
- [ ] Relevant CI gates pass.
- [ ] Schema validation passes.
- [ ] Deterministic outputs verified where relevant.
- [ ] Run manifests include commit/config/input metadata where relevant.

### 3. Benchmarks

- [ ] `docs/METRICS_CURRENT.md` updated if metrics changed.
- [ ] Benchmark commands recorded.
- [ ] Cheap-baseline comparisons included for advanced methods.
- [ ] Benchmark failures or regressions documented.
- [ ] Benchmark governance status clear: exploratory, informational, gate, deprecated.

### 4. Evidence and claims

- [ ] Claims mapped to `docs/PROOF_LADDER.md`.
- [ ] Dry-lab outputs are not described as biological proof.
- [ ] Unsupported claims listed or avoided.
- [ ] Positive evidence is not overgeneralized.
- [ ] Negative evidence is preserved where safe.

### 5. Safety

- [ ] `SAFETY.md` still matches release behavior.
- [ ] `RESPONSIBLE_USE.md` still matches release behavior.
- [ ] `MODEL_RELEASE_POLICY.md` applied to models, candidates, or sensitive artifacts.
- [ ] No wet-lab protocols or operational biological instructions added.
- [ ] No harmful optimization objective added.
- [ ] Candidate/model release status explicit.
- [ ] Safety review recorded if needed.

### 6. Data and licenses

- [ ] New data has dataset cards.
- [ ] License/terms are documented.
- [ ] Redistribution status is clear.
- [ ] Citation requirements are included.
- [ ] Restricted data is not committed.

### 7. Models and adapters

- [ ] New models/adapters have model cards.
- [ ] External adapters do not silently send sequences to third parties.
- [ ] Missing dependencies fail closed.
- [ ] Model limitations are documented.
- [ ] Release decision is recorded.

### 8. External-facing artifacts

- [ ] External review packet generated if needed.
- [ ] Candidate handoff is non-protocol and expert-review oriented.
- [ ] Pre-registration exists for pilot-facing work.
- [ ] Result-intake schema is referenced if results are expected.
- [ ] Publication/release boundaries are clear.

### 9. Agent and maintainer readiness

- [ ] `docs/PROJECT_INDEX.md` updated if docs changed.
- [ ] `README.md` updated if entrypoint changed.
- [ ] `docs/HIGH_LEVERAGE_TASKS.md` or `docs/NEXT_100_PR_MAP.md` updated if strategy changed.
- [ ] Issue templates/labels still match workflow.
- [ ] Maintainer decision logs created for major decisions.

## Release note template

```md
# Release <version>

## What changed

...

## Evidence

- Tests:
- Benchmarks:
- Baselines:
- Schemas:

## Safety impact

...

## Claim level

Mapped to `docs/PROOF_LADDER.md`: Level <n>.

## What this does not prove

...

## Known failures and limitations

...

## Artifact release status

| Artifact | Status | Reason |
|---|---|---|
| ... | open/staged/restricted/internal | ... |

## Next bottleneck

...
```

## Red flags before release

Stop release if:

- benchmark failure is hidden;
- claim language exceeds proof level;
- safety review is missing for sensitive artifacts;
- external-facing docs include operational wet-lab details;
- candidate release status is unclear;
- new data lacks license review;
- model/adapters lack cards;
- agents changed safety-sensitive content without human review;
- release notes only describe success.

## Post-release checklist

After release:

- [ ] Tag or version recorded.
- [ ] Release notes published.
- [ ] Known limitations visible.
- [ ] Issues created for next bottlenecks.
- [ ] Docs index updated.
- [ ] Any safety-sensitive follow-up tracked.

## Final standard

A release should make OpenAMP easier to trust even when the release contains disappointing results.

That is the standard for scientific infrastructure.
