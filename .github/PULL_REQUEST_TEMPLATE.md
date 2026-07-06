## Description

<!-- What does this PR do? What bottleneck does it remove? -->

## Change class

- [ ] Class A — safe documentation or small bug fix
- [ ] Class B — infrastructure / schema / CLI / report change
- [ ] Class C — scientific behavior change: scoring, selection, benchmark, calibration, simulation
- [ ] Class D — safety-sensitive or wet-lab-facing change

See `docs/getting-started/MAINTAINER_GUIDE.md`.

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] New scorer / predictor / simulation module
- [ ] New or changed benchmark
- [ ] Documentation update
- [ ] Safety policy change
- [ ] Infrastructure / CI / tooling
- [ ] Agent/onboarding improvement
- [ ] External-review / collaboration artifact

## Safety impact

- [ ] No biological misuse capability added
- [ ] No wet-lab protocol or operational biological procedure added
- [ ] No harmful optimization objective added
- [ ] No unscreened candidate sequences published
- [ ] No model weights or sensitive artifacts released without policy review
- [ ] No efficacy, safety, clinical, or therapeutic claims without evidence
- [ ] Limitations and failure modes documented
- [ ] Evidence is reproducible where applicable
- [ ] Human safety review requested if this is safety-sensitive

## Claim discipline

- [ ] Claims are mapped to `docs/PROOF_LADDER.md`
- [ ] Dry-lab outputs are not described as biological proof
- [ ] No “AI discovered an antibiotic” / “drug candidate” / “safe” / “clinically useful” language unless evidence level supports it
- [ ] Unsupported claims are explicitly listed or avoided

## Baseline and benchmark discipline

Required for scorer, predictor, simulator, ranking, calibration, active-learning, or benchmark changes.

- [ ] Cheapest meaningful baseline identified
- [ ] Baseline comparison included or change is explicitly informational only
- [ ] Benchmark leakage or shortcut risks considered
- [ ] `docs/evidence/METRICS_CURRENT.md` updated if metrics changed
- [ ] `docs/evidence/BENCHMARKING.md` / `docs/evidence/BENCHMARK_GOVERNANCE.md` updated if benchmark behavior changed

## Verification

- [ ] `make ci` passes
- [ ] `make bench-gate` passes if benchmark-sensitive
- [ ] Tests added for new functionality
- [ ] Existing tests updated to match behavior changes
- [ ] Documentation updated if behavior changed
- [ ] Determinism confirmed (`make regenerate-all` if pipeline logic changed)
- [ ] Schema validation passes if artifacts changed

## Agent disclosure

- [ ] This PR was not agent-generated
- [ ] This PR was fully or partly agent-generated and human-reviewed
- [ ] Agent-generated changes stayed within `docs/getting-started/AGENT_ONBOARDING.md` boundaries

## Evidence

<!-- What evidence supports the change? Include commands, test names, benchmark outputs, limitations, and what this does NOT prove. -->

## External or wet-lab-facing impact

- [ ] Not applicable
- [ ] Affects external review packet / handoff / pilot planning
- [ ] Requires domain expert review
- [ ] Requires safety review
- [ ] Does not include operational experimental instructions

## Dependencies and licenses

<!-- List any new dependencies, model artifacts, or data sources and their license/release status. -->

- None

## Reviewer focus

<!-- Tell reviewers where to be skeptical. -->
