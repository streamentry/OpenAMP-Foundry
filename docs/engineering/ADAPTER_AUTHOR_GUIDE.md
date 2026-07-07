# Adapter Author Guide

## Purpose

This guide explains how to add external predictors, scorers, simulators, or data/tool adapters to OpenAMP Foundry without weakening safety, privacy, reproducibility, or benchmark honesty.

Adapters are powerful because they make the repo extensible.

Adapters are risky because they can quietly import unreviewed claims, dependencies, network calls, or release problems.

## Prime rule

**An adapter is a translation layer, not a trust guarantee.**

If an external tool is wrapped by OpenAMP, its outputs still need scope, uncertainty, benchmark comparison, and release review.

## What adapters may do

Adapters may:

- call a local external tool;
- wrap a transparent heuristic;
- normalize third-party predictor output;
- import public metadata with license review;
- expose uncertainty or failure status;
- add informational report fields;
- support benchmark comparison.

Adapters may not:

- silently transmit sequences or sensitive metadata;
- silently download model weights;
- bypass release policy;
- strengthen claims by default;
- affect ranking without gates;
- hide failures or missing dependencies;
- publish restricted outputs.

## Required adapter card

Every adapter should have a model/adapter card using [`MODEL_CARD_TEMPLATE.md`](../trust/MODEL_CARD_TEMPLATE.md).

The card must include:

- intended use;
- not-for list;
- whether it runs locally or remotely;
- inputs and outputs;
- data sent outside the local environment, if any;
- dependency and license status;
- benchmark and cheap-baseline comparison;
- failure behavior;
- release decision;
- known limitations.

## Adapter modes

| Mode | Meaning | Ranking authority |
|---|---|---|
| `off` | Adapter disabled. | None. |
| `info` | Adapter output may appear in reports. | None. |
| `gated` | Adapter may be considered only if required benchmark and safety gates pass. | Conditional. |
| `deprecated` | Adapter should not be used for new work. | None. |

Default mode should be `off` or `info`.

## Privacy and network policy

Adapters must not make silent network calls.

If a remote service is used, the adapter must document:

- what data is transmitted;
- who receives it;
- whether sequences are included;
- whether metadata is included;
- terms of service or license status;
- how users explicitly opt in;
- how failures are handled.

A local-only adapter is preferred when possible.

## Failure behavior

Adapters should fail closed.

Failure should produce an explicit status such as:

- dependency missing;
- external tool unavailable;
- unsupported input;
- timeout;
- invalid output;
- uncertainty too high;
- license or release status unknown.

Do not silently substitute success-like defaults.

## Benchmark requirement

Before an adapter can influence ranking, it must be challenged by a cheap baseline.

Examples:

| Adapter type | Cheap enemy |
|---|---|
| Activity predictor | charge density, length, similarity. |
| Selectivity predictor | simple selectivity proxy. |
| Structure proxy | simple helix propensity. |
| Novelty tool | nearest-neighbor similarity. |
| Synthesis feasibility tool | simple length/composition flags. |
| Result emulator | previous selection policy. |

If the adapter fails to beat the cheap enemy, it may remain informational.

## Output contract

Adapter outputs should include:

```yaml
adapter_id: stable-id
adapter_version: version
mode: off | info | gated | deprecated
input_hash: sha256-or-null
output_status: ok | warning | error | unavailable
score_fields: map
uncertainty: value-or-null
warnings: list
failure_reason: text-or-null
release_status: open | staged | restricted | internal | do-not-release
ranking_effect: none | proposed | active
```

## Human review triggers

Human review is required when an adapter:

- sends data outside the local environment;
- changes ranking behavior;
- uses non-toy biological data;
- adds model artifacts;
- changes release status;
- affects candidate or partner-facing artifacts;
- could be interpreted as validation.

## Agent guidance

Agents may scaffold adapters and cards.

Agents must not autonomously enable ranking authority, add remote calls, commit model weights, or change release status.

## Final standard

A good adapter makes external tools easier to evaluate without making them easier to overtrust.
