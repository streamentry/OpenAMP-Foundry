# Model and Adapter Card Template

## Purpose

This template defines the minimum documentation required before any model, scorer, predictor, simulator, adapter, or generator is trusted inside OpenAMP Foundry.

A model without a card is not an OpenAMP component. It is an unreviewed artifact.

## Prime rule

**A model card must make it clear what the model must not be used for.**

## Card metadata

```yaml
model_id: stable-id
name: human-readable name
artifact_type: scorer | predictor | simulator | generator | adapter | baseline
status: experimental | informational | gate-eligible | production | deprecated
version: MAJOR.MINOR.PATCH
created_at: YYYY-MM-DD
maintainer: person-or-role
repo_commit: git-sha
release_status: open | staged | restricted | internal | do-not-release
proof_ladder_limit: maximum claim level this model can support
```

## Intended use

State exactly what the component is for.

Examples:

- score candidate AMP-likeness for dry-lab triage;
- flag safety-risk concerns for expert review;
- compare candidates against a cheap baseline;
- provide experimental context in reports;
- generate toy candidates for demos;
- adapt an external predictor into the OpenAMP artifact format.

## Not for

State what the model must not be used for.

Common non-uses:

- proving biological activity;
- proving human safety;
- clinical decision-making;
- therapeutic claims;
- unreviewed candidate release;
- harmful biological optimization;
- bypassing qualified expert review;
- replacing wet-lab validation;
- ranking candidates if the component is informational only.

## Inputs

Document:

- required input fields;
- accepted sequence alphabet or representation;
- length limits;
- metadata requirements;
- whether full sequences are sent to external services;
- whether inputs may be sensitive.

## Outputs

Document:

- score fields;
- uncertainty fields;
- warnings;
- failure modes;
- release flags;
- evidence-certificate integration;
- whether output may affect ranking.

## Training or calibration data

If applicable, document:

- dataset IDs;
- dataset cards;
- training/validation/test split;
- leakage controls;
- label definitions;
- known biases;
- redistribution status;
- whether restricted data was used.

If no training data exists because the component is heuristic, say so.

## Benchmarks

Every nontrivial component should answer:

| Question | Answer |
|---|---|
| What benchmark tests this component? | TBD |
| What cheap baseline challenges it? | TBD |
| Does it beat the baseline? | yes / no / partial / unknown |
| Can it affect ranking? | yes / no / gated |
| What failure downgraded it? | TBD |
| Where are metrics recorded? | `docs/evidence/METRICS_CURRENT.md` |

A component that fails its cheap baseline may remain informational, but must not silently gain authority.

## Safety assessment

Answer:

1. Could this component increase biological misuse capability?
2. Could it optimize harmful traits?
3. Could it produce unscreened candidate lists?
4. Could outputs be misread as biological proof?
5. Does it require staged or restricted release?
6. Does it send data outside the local machine?
7. Does it require human review before use?

## Release decision

Choose one:

- open release;
- staged release;
- restricted release;
- metadata-only release;
- local-only artifact;
- do not release.

Explain why.

## Known limitations

List limitations aggressively.

Good limitations are specific:

- “May mostly learn charge density.”
- “Weak on non-helical AMPs.”
- “No calibration against qualified outcomes.”
- “Fails within-AMP hemolysis benchmark.”
- “Requires external tool not available in CI.”
- “Can provide context but not ranking authority.”

Bad limitations are vague:

- “May be imperfect.”
- “Needs more data.”

## Failure behavior

Document what happens when:

- inputs are invalid;
- dependencies are missing;
- external service fails;
- uncertainty is too high;
- benchmark artifacts are missing;
- safety flags are triggered;
- model output is outside expected range.

Preferred behavior is fail-closed.

## Human review

Record:

| Review type | Reviewer | Date | Decision |
|---|---|---|---|
| Scientific review | TBD | TBD | approve / revise / reject |
| Benchmark review | TBD | TBD | approve / revise / reject |
| Safety review | TBD | TBD | approve / staged / restrict / reject |
| Maintainer review | TBD | TBD | approve / revise / reject |

## Example card skeleton

```md
# Model Card: <name>

## Status

Experimental / informational / production / deprecated.

## Intended use

...

## Not for

...

## Inputs and outputs

...

## Data

...

## Benchmarks and baselines

...

## Safety and release

...

## Limitations

...

## Failure behavior

...

## Review record

...
```

## Final standard

A model card should make an impressive model easier to distrust correctly.

That is how OpenAMP turns models into infrastructure components instead of hype objects.
