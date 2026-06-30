# OpenAMP Foundry — Detailed Plan

## 1. Mission

Build a responsible, verification-first, computer-first antimicrobial peptide discovery pipeline.

The project goal is **not** to claim that computers can prove biological efficacy. The goal is to create a reproducible dry-lab funnel that reduces the number of weak, unsafe, duplicate, or non-synthesizable candidates before any lab spending.

Core thesis:

> AI generation is cheap. Trusted candidate selection is scarce.

Longer term:

> Wet-lab time is expensive. The project should learn how to spend it only where the evidence says it matters most.

## 2. World-history ambition, narrowed to a tractable wedge

The world-scale problem is antimicrobial resistance. The tractable wedge is not “solve AMR.” The tractable wedge is:

> Build an auditable AMP candidate foundry that can generate, rank, falsify, and document candidates before independent assay.

The first historical-grade contribution would be a reproducible pipeline that:

1. passes leakage-resistant retrospective benchmarks;
2. produces candidate evidence certificates;
3. sends a small, pre-registered shortlist to independent assay;
4. publishes both hits and failures;
5. improves through active learning without cherry-picking.

The next historical-grade contribution would be stronger:

> Build an open wet-lab compression engine for AMPs that measurably improves experiment selection using calibrated virtual assay layers and small, honest feedback loops.

## 3. Non-negotiable scientific principles

| Principle | Meaning |
|---|---|
| No biological proof without assay | Computational scores are only triage evidence |
| Pre-register ranking rules | Do not change selection criteria after seeing results |
| Publish negative results when safe | Prevents duplicated scientific waste |
| Separate generator from judge | Avoid self-confirming model loops |
| Prefer independent scorers | Model disagreement is information |
| Penalize toxicity early | Activity without safety is not valuable |
| Audit novelty | Do not rediscover known motifs and call them new |
| Avoid dangerous scope | No pathogen enhancement, no harmful objective functions |

## 4. MVP milestone

### MVP statement

Input 10,000 peptide sequences and output a ranked top 100 with machine-readable evidence certificates.

### MVP success criteria

| Test | Required result |
|---|---|
| Validity | Invalid sequences rejected |
| Feature extraction | Basic physicochemical values computed reproducibly |
| Novelty | Near-duplicates of known references flagged |
| Baseline ranking | Ranking is deterministic and explainable |
| Evidence | Every selected candidate has a JSON certificate |
| Schema | Certificates validate against JSON schema |
| Demo | `make demo` completes on toy data |

### MVP non-goals

- No wet-lab protocol.
- No trained generator weights.
- No claims of efficacy.
- No dangerous pathogens.
- No clinical language.
- No production medical recommendations.

## 5. Architecture

```text
Candidate source
  -> normalize sequence
  -> validate amino-acid alphabet
  -> compute features
  -> score activity-likeness
  -> score safety-risk
  -> score synthesis-feasibility
  -> score novelty against reference set
  -> compute ensemble score
  -> diversity selection
  -> generate evidence certificate
  -> human review
  -> optional lab batch decision
```

Future architecture extension:

```text
candidate source
  -> current dry-lab foundry
  -> membrane/selectivity/stability proxy models
  -> uncertainty estimation
  -> informative assay batch selection
  -> lab result ingestion
  -> calibration / active learning
  -> next-round candidate source
```

## 6. Scoring model in v0.1

The v0.1 scorer is intentionally simple. It is not a scientific predictor. It is a transparent baseline.

| Score | Purpose | v0.1 method |
|---|---|---|
| Activity-likeness | Rank AMP-like sequences | Charge, hydrophobicity, amphipathic proxy, length |
| Safety risk | Penalize obviously risky candidates | Hydrophobicity excess, extreme charge, motifs, length |
| Synthesis feasibility | Penalize difficult candidates | Length, noncanonical symbols, unusual residues |
| Novelty | Avoid duplicates | Sequence identity / normalized edit distance against references |
| Ensemble | Rank survivors | Weighted score from config |

Later versions should replace or supplement these with independent open predictors.

## 7. Dry-lab verification ladder

| Level | Evidence type | Meaning |
|---:|---|---|
| 0 | Syntax validity | Candidate is a valid peptide sequence |
| 1 | Reproducible features | Features are deterministic and versioned |
| 2 | Baseline score | Transparent heuristic survives basic filters |
| 3 | Multi-model consensus | Independent predictors agree |
| 4 | Leakage-resistant retrospective benchmark | Pipeline recovers hidden positives without cheating |
| 5 | Lab assay | Independent biological validation |
| 6 | Replication | Separate lab reproduces result |

This repo starts at levels 0–2 and creates scaffolding for levels 3–6.

## 8. Six-phase roadmap

### Phase 0 — Safe skeleton

Deliverables:

- repo structure;
- safety policy;
- license policy;
- JSON schemas;
- toy demo pipeline;
- tests and CI.

Exit criterion:

```text
make demo && make test
```

### Phase 1 — Data foundation

Deliverables:

- fetch scripts for allowed public AMP datasets;
- license-aware metadata;
- deduplication;
- sequence normalization;
- cluster splitting;
- leakage checks;
- negative-set construction policy.

Exit criterion:

```text
A dataset card exists for every dataset, including source, license, date, labels, known bias, and redistribution status.
```

### Phase 2 — Honest benchmark

Deliverables:

- baseline predictors;
- time split where possible;
- cluster split by sequence similarity;
- hidden-positive recovery benchmark;
- negative-control benchmark;
- toxicity penalty benchmark;
- public report template.

Exit criterion:

```text
The baseline system beats simple charge/hydrophobicity baselines without leakage.
```

### Phase 3 — Multi-model dry-lab foundry

Deliverables:

- adapters for external AMP predictors;
- optional protein-language-model embeddings;
- model version manifest;
- ensemble ranker;
- uncertainty and disagreement scores;
- top-candidate evidence certificates.

Exit criterion:

```text
The system generates a top 50–100 shortlist with evidence, uncertainty, and failure modes.
```

### Phase 4 — External assay-ready package

Deliverables:

- pre-registered selection rule;
- candidate batch manifest;
- assay recommendation fields;
- independent review checklist;
- negative-control candidate list;
- publication-ready methods appendix.

Exit criterion:

```text
A microbiologist can review the batch and say whether it is worth assay money.
```

### Phase 5 — Active-learning loop

Deliverables:

- lab result ingestion schema;
- hit/failure learning module;
- model update report;
- second-batch selection;
- public negative-result archive where safe.

Exit criterion:

```text
Second-batch hit rate improves over first-batch hit rate without changing success definitions after the fact.
```

### Phase 6 — Scientific credibility

Deliverables:

- independent replication;
- preprint or paper;
- public benchmark release;
- safe release of validated candidate families;
- non-cherry-picked failure archive.

Exit criterion:

```text
At least one candidate family survives independent validation and is documented with computational and lab evidence.
```

### Phase 7 — Wet-lab compression

Deliverables:

- virtual assay specification with explicit scope limits;
- membrane/selectivity proxy benchmark set;
- calibration harness for ingesting wet-lab outcomes;
- uncertainty-aware simulator outputs;
- active-learning selection policy;
- experiment-saved evaluation metric.

Exit criterion:

```text
The project shows that the added modeling layer improves which experiments are chosen next better than cheap-predictor-only baselines.
```

## 9. Governance and release model

### Open immediately

- core pipeline code;
- schemas;
- benchmark methodology;
- safety filters;
- evidence certificate generator;
- toy datasets;
- documentation.

### Delayed or restricted

- high-throughput generator weights;
- unscreened top candidate sequences;
- objective functions that could be repurposed for toxicity optimization;
- dangerous organism protocols;
- any content that materially increases biological misuse capability.

## 10. First 14-day execution plan

### Day 1–2

- Run demo pipeline.
- Read `SAFETY.md` and `RESPONSIBLE_USE.md`.
- Choose repo name and public positioning.
- Remove anything you cannot defend publicly.

### Day 3–4

- Replace toy data with license-permitted public dataset loaders.
- Add dataset cards.
- Implement deduplication.
- Implement sequence clustering.

### Day 5–7

- Add stronger baseline predictors.
- Add leakage checks.
- Add negative-set policy.
- Add benchmark report output.

### Day 8–10

- Add evidence certificates for each selected candidate.
- Add model/version manifest.
- Add pre-registration template for lab batch selection.

### Day 11–14

- Run retrospective benchmark.
- Write public benchmark report.
- Decide whether the pipeline has enough signal to justify external expert review.

## 11. Kill criteria

Stop or redesign if any are true:

| Kill condition | Reason |
|---|---|
| Ranking cannot beat trivial baselines | No signal |
| High scores are explained by near-duplicates | Leakage / novelty failure |
| Toxicity screen removes almost all top candidates | Activity-only optimization is weak |
| Results are unstable across splits | Model is not robust |
| Candidate certificates cannot explain ranking | Not reviewable |
| A microbiologist says the batch is scientifically naive | Domain gap too large |

## 12. Strongest counterargument

The strongest objection is that AMP prediction has many biased datasets and easy-to-overfit benchmarks. A naive model can look excellent while merely learning charge, length, hydrophobicity, or dataset artifacts.

The answer is not “use bigger models.”

The answer is:

- better negative sets;
- cluster/time splits;
- leakage checks;
- transparent baselines;
- independent assay;
- publication of failures.

## 13. Final strategic position

Do not claim:

> AI discovered antibiotics.

Claim:

> We are building an auditable dry-lab foundry that makes AMP candidate selection reproducible, safety-aware, and cheaper to validate experimentally.

That is scientifically defensible and still ambitious.
