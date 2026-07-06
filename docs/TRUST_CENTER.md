# Trust Center

## Purpose

This document is the trust front door for OpenAMP Foundry.

It summarizes why a serious human, AI agent, lab, institution, funder, or safety reviewer can evaluate this repository without relying on maintainer confidence.

OpenAMP is trying to become open biotech infrastructure. Infrastructure requires trust before scale.

## One-sentence trust promise

**OpenAMP will make every important candidate-selection claim auditable, every safety boundary explicit, every benchmark vulnerable to cheap-baseline challenge, and every failure useful when safe to preserve.**

## What trust means here

Trust does not mean believing the model.

Trust means a reviewer can inspect:

- what the model saw;
- what the model did;
- what baselines challenged it;
- what gates blocked it;
- what evidence level supports each claim;
- what safety boundary applies;
- what uncertainty remains;
- what negative results were preserved;
- what decision a human reviewer made.

## Trust surfaces

OpenAMP has several trust surfaces.

| Surface | Trust question | Source of truth |
|---|---|---|
| Safety | Could this increase misuse risk? | `SAFETY.md`, `RESPONSIBLE_USE.md`, `MODEL_RELEASE_POLICY.md` |
| Claims | Does wording exceed evidence? | `docs/PROOF_LADDER.md` |
| Benchmarks | Could the result be shortcut-driven? | `docs/BENCHMARK_GOVERNANCE.md`, `docs/METRICS_CURRENT.md` |
| Candidates | Why was this candidate selected? | `docs/EVIDENCE_CERTIFICATE.md` |
| External review | Can outsiders reject the package? | `docs/EXTERNAL_REVIEW_PACKET.md` |
| Data | Can the data be used and redistributed? | `DATA_LICENSE_NOTICE.md`, `docs/DATA_GOVERNANCE.md` |
| Models | Should this model/artifact be released? | `MODEL_RELEASE_POLICY.md`, `docs/MODEL_CARD_TEMPLATE.md` |
| Calibration | Can the system update without cherry-picking? | `docs/CALIBRATION_POLICY.md` |
| Agents | Can agents work safely? | `AGENTS.md`, `docs/AGENT_ONBOARDING.md` |
| Maintainers | Can the project survive growth? | `docs/MAINTAINER_GUIDE.md`, `docs/RELEASE_CHECKLIST.md` |

## Trust architecture

```text
safe scope
  -> toy defaults
  -> deterministic pipeline
  -> evidence certificates
  -> benchmark governance
  -> proof ladder
  -> external review packets
  -> structured result intake
  -> recalibration gate
  -> human decision logs
  -> release checklist
```

Each layer exists because the previous layer is insufficient alone.

## Safety posture

OpenAMP is dry-lab by default.

It does not exist to provide wet-lab protocols, pathogen-handling instructions, clinical advice, harmful optimization objectives, or unrestricted release of sensitive biological artifacts.

The safe boundary is:

> OpenAMP packages computational evidence for qualified expert review. It does not instruct unqualified biological experimentation.

## Evidence posture

OpenAMP treats all computational outputs as hypotheses.

Dry-lab scores can nominate candidates for review. They do not prove activity, safety, therapeutic value, or clinical relevance.

The project’s highest-status behavior is claim downgrading when evidence is weak.

## Benchmark posture

Every advanced method needs a cheap enemy.

If a scorer, simulator, predictor, selector, or calibration update does not beat a simple baseline under fair conditions, it may remain informational, but it should not gain authority.

This is not pessimism. It is infrastructure hygiene.

## Release posture

Open does not mean reckless.

Open by default:

- code;
- schemas;
- validators;
- benchmark infrastructure;
- transparent baseline scorers;
- toy/demo data;
- documentation;
- safety filters;
- evidence and review formats.

Reviewed before release:

- candidate panels;
- non-toy biological datasets;
- external model artifacts;
- generator weights;
- high-throughput outputs;
- wet-lab-facing summaries;
- any artifact that could materially increase misuse risk.

## Agent posture

Agents are useful for infrastructure, not autonomous biological authority.

Best agent work:

- tests;
- validators;
- schemas;
- docs;
- benchmarks;
- baseline comparisons;
- report generation;
- consistency checks;
- reproducibility improvements.

Human review required for:

- safety policy;
- candidate release;
- model release;
- wet-lab-facing artifacts;
- benchmark thresholds;
- calibration policy;
- claim strengthening.

## External reviewer posture

OpenAMP should invite hostile review.

A good external review should be able to say:

- this candidate is a near-duplicate;
- this score is shortcut-driven;
- this benchmark is weak;
- this safety boundary is insufficient;
- this release should be staged;
- this claim should be downgraded;
- this pilot is not ready.

Rejection is not embarrassment. It is quality control.

## Trust metrics

The project should eventually track:

- number of schema-valid evidence certificates;
- number of benchmark cards;
- number of benchmarks with cheap-baseline comparisons;
- number of safety-reviewed releases;
- number of external review packets;
- number of negative results preserved where safe;
- number of recalibration rejections;
- number of agent-safe issues completed with tests;
- number of external artifact reuses;
- number of claims downgraded after review.

Stars are weak evidence.

Reusable artifacts and external critique are strong evidence.

## Trust failures

The project loses trust when:

- dry-lab scores are described as biology;
- candidate sequences are released without review;
- operational wet-lab instructions creep into docs;
- benchmark thresholds move silently;
- negative results disappear;
- safety is treated as marketing;
- agents are allowed to broaden scope without review;
- release decisions lack records;
- maintainers defend a story instead of evidence.

## What a trustworthy OpenAMP release should include

A serious release should say:

- what changed;
- what evidence supports it;
- what benchmarks passed or failed;
- what claims changed;
- what safety review occurred;
- what artifacts are open, staged, restricted, or withheld;
- what remains unproven;
- what the next bottleneck is.

## Final standard

OpenAMP should be the repo that serious people trust because it makes trust expensive to fake.

That is the foundation for becoming the number-one open infrastructure layer for trustworthy antimicrobial peptide experiment selection.
