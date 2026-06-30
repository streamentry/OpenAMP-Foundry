# OpenAMP Foundry — Mission for AI Agents

## Ultimate Goal

Build a verification-first AI antimicrobial peptide discovery foundry that can produce a result worthy of serious global scientific attention:

> **Discover a novel antimicrobial peptide family, generated and selected by an open AI pipeline, that is independently validated to inhibit drug-resistant bacteria while showing low mammalian toxicity, with the full computational evidence trail, negative results, benchmark methodology, and candidate-selection process made reproducible.**

The goal is not to claim “AI discovered a drug.”

The goal is stronger and more honest:

> **AI found a new, experimentally validated antimicrobial candidate family through a reproducible, auditable, safety-first discovery pipeline.**

A headline-grade result requires **independent wet-lab confirmation**. Computational scores alone are never enough.

## Legacy Ambition

The deepest ambition of this project is larger than finding one good peptide.

The long-range contribution worth building a legacy around is:

> **Make wet-lab antimicrobial discovery partially computable by building an open, reproducible system that learns which experiments are worth running.**

That means OpenAMP should evolve from a dry-lab ranking pipeline into a **wet-lab compression engine**:

```text
design
→ falsify
→ simulate
→ prioritize
→ test
→ learn
→ redesign
```

The near-term promise is not “replace biology.”

The near-term promise is:

> **Use computation to reduce the number of wet-lab experiments needed to find a real antimicrobial signal by 10x, if the evidence honestly supports that claim.**

This ambition does not weaken the repo’s current safety posture. It raises the bar for what the project should eventually become.

---

# North Star

The project exists to answer one question:

> Can an AI-directed, open, reproducible, safety-constrained dry-lab pipeline discover antimicrobial candidates that survive real experimental validation better than ordinary human/manual search?

If yes, this becomes a serious scientific contribution.

If no, the project should still create value by publishing clean benchmarks, failed candidates, leakage checks, evidence schemas, and reproducible negative results.

---

# What Counts as a World-Headline Result

A legitimate headline-grade result must meet all of these conditions:

| Requirement            | Minimum standard                                                                                           |
| ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| Novelty                | Candidate family is not a trivial near-duplicate of known AMPs                                             |
| Activity               | At least one candidate shows meaningful antimicrobial activity in lab assay                                |
| Safety                 | Candidate shows low hemolysis / low mammalian cytotoxicity in initial screening                            |
| Resistance relevance   | Tested against clinically relevant resistant or hard-to-treat bacterial strains through qualified partners |
| Reproducibility        | Full dry-lab pipeline can be rerun from versioned inputs                                                   |
| Evidence               | Every selected candidate has a machine-readable evidence certificate                                       |
| Independent validation | At least one external lab or CRO reproduces the key result                                                 |
| Scientific honesty     | Negative results and failed candidates are documented                                                      |
| Safety                 | No dangerous protocol, pathogen-enabling instruction, or misuse-oriented optimization is published         |
| Public value           | Results are released under a responsible open-science policy                                               |

Do not optimize for hype. Optimize for a result that survives hostile scientific review.

---

# Core Scientific Bet

AI is not being used as magic.

AI is being used for:

1. Generating candidate peptide sequences.
2. Filtering invalid or low-quality candidates.
3. Scoring predicted antimicrobial activity.
4. Penalizing predicted toxicity.
5. Checking novelty against known peptide databases.
6. Selecting diverse candidates for testing.
7. Producing evidence certificates.
8. Learning from failed assays.
9. Improving candidate selection over repeated cycles.

The lab remains the judge.

The computer pipeline is the triage engine.

## Second-Horizon Scientific Bet

The current pipeline is the first layer, not the endpoint.

The next serious scientific leap is to build a **multi-resolution virtual assay layer** that predicts which candidates are worth spending lab budget on:

```text
peptide sequence
↓
structure / conformation proxies
↓
bacterial membrane interaction model
↓
RBC / mammalian membrane interaction model
↓
stability / protease / serum model
↓
learned surrogate for assay outcomes
↓
selection of the few most informative real experiments
```

This is not a claim that OpenAMP can simulate a whole organism or replace qualified assay work.

It is a claim that, over time, the project may become good at **experimental compression**:

> asking fewer, smarter wet-lab questions while preserving scientific honesty.

---

# Primary Target

Initial target:

> **Short antimicrobial peptides, approximately 10–30 amino acids, optimized for novelty, predicted antimicrobial activity, low hemolysis risk, low cytotoxicity risk, synthesis feasibility, and diversity.**

Do not begin with broad “AI for antibiotics.”

Do not begin with human therapeutics claims.

Do not begin with dangerous pathogens.

The first target is a safe, constrained, reproducible discovery loop.

---

# Definition of Done: Phase 1

Phase 1 is complete only when the project can do this:

```text
Input:
  Candidate peptide sequences

Pipeline:
  Validate sequence
  Extract physicochemical features
  Score antimicrobial likelihood
  Score toxicity / hemolysis risk
  Score novelty against known AMP references
  Score synthesis feasibility
  Select diverse top candidates
  Generate evidence certificates

Output:
  Ranked candidate batch
  Candidate evidence JSON files
  Batch report
  Benchmark report
  Reproducible run manifest
```

Minimum success:

* Pipeline runs from a clean checkout.
* Tests pass.
* Candidate reports are deterministic.
* Evidence certificates validate against JSON Schema.
* Benchmark avoids obvious train/test leakage.
* Known active peptides are ranked better than random baseline.
* Known negative or toxic examples are penalized.

---

# Definition of Done: Phase 2

Phase 2 is complete only when the system passes retrospective validation.

Required tests:

| Test                    | Required result                                                                           |
| ----------------------- | ----------------------------------------------------------------------------------------- |
| Hidden active recovery  | Known active AMPs hidden from training appear disproportionately in top-ranked candidates |
| Negative-set robustness | Performance remains meaningful across multiple negative datasets                          |
| Cluster split           | Pipeline still performs when near-duplicates are removed                                  |
| Novelty pressure        | Top candidates are not merely copies of known AMP motifs                                  |
| Toxicity penalty        | Predicted hemolytic/toxic candidates are down-ranked                                      |
| Ablation                | Removing safety/novelty filters makes results worse or riskier                            |
| Reproducibility         | Another machine can reproduce rankings from the same inputs                               |

If the pipeline cannot beat simple baselines honestly, do not proceed to lab testing.

## Definition of Done: Phase 2.5

Phase 2.5 begins when the dry-lab system is credible enough to support a higher-fidelity virtual assay roadmap.

Required deliverables:

| Deliverable | Required result |
| ----------- | --------------- |
| Simulator specification | Written scope for what is and is not being modeled |
| Membrane proxy benchmark | Distinguishes bacterial-selective vs clearly hemolytic reference peptides better than naive heuristics |
| Calibration plan | Explicit plan for learning from small real assay batches |
| Uncertainty policy | Simulator outputs include confidence and “do not trust” conditions |
| Safety policy | No release of high-capability components without human review |

If a virtual-assay module cannot outperform simple heuristics for triage, it must remain experimental and must not be presented as a scientific breakthrough.

---

# Definition of Done: Phase 3

Phase 3 is complete only when a lab-ready candidate batch exists.

A lab-ready batch must include:

1. 50–100 selected candidate peptides.
2. Full evidence certificate for every candidate.
3. Diversity clustering report.
4. Novelty report against known AMP references.
5. Predicted toxicity / hemolysis risk report.
6. Synthesis feasibility report.
7. Pre-registered selection rule.
8. Pre-registered pass/fail criteria.
9. Risk review.
10. Independent review by at least one qualified microbiology or peptide expert.

No cherry-picking after seeing results.

No changing the scoring rule after candidate selection.

---

# Definition of Done: Phase 4

Phase 4 is complete only after qualified external testing.

The project must not publish biological claims until:

* candidates are synthesized or obtained through legitimate qualified providers;
* assays are performed by qualified labs or CROs;
* results include positive controls and negative controls;
* raw result summaries are preserved;
* failures are recorded;
* at least one promising hit is retested;
* the best result is independently reproduced.

The project may say:

> “Computationally nominated candidate.”

It may not say:

> “Antibiotic,” “drug,” “cure,” or “clinically useful therapy”

unless the relevant biological and clinical evidence exists.

---

# Definition of Done: Headline-Grade Result

A result is headline-grade only if all of the following are true:

```text
1. A novel peptide family is discovered by the pipeline.
2. The family is not a trivial near-duplicate of known AMPs.
3. Multiple related candidates show antimicrobial activity.
4. At least one candidate shows low mammalian toxicity in initial tests.
5. Activity is reproduced by an independent lab or CRO.
6. The dry-lab selection pipeline is fully reproducible.
7. The candidate evidence certificates are public or reviewable.
8. The project publishes negative results and failed candidates where safe.
9. Claims are reviewed by qualified domain experts.
10. Safety review confirms that release does not materially enable misuse.
```

Only then may the project claim:

> “An open AI discovery pipeline produced a newly validated antimicrobial peptide family.”

---

# Agent Operating Principles

AI agents working on this repo must obey these principles.

## 1. Evidence before confidence

Every claim must be backed by one of:

* code;
* test result;
* benchmark result;
* dataset reference;
* evidence certificate;
* reproducible command;
* literature citation;
* expert review note.

Unsupported claims must be marked as speculation or removed.

## 2. The lab is the judge

Computational scores are not biological proof.

Never describe a candidate as effective, safe, therapeutic, drug-like, or clinically useful unless experimental evidence supports that exact claim.

## 3. No cherry-picking

Agents must preserve:

* failed candidates;
* rejected candidates;
* benchmark failures;
* model disagreements;
* negative results;
* known limitations.

A clean failure is more valuable than a fake success.

## 4. Safety-first optimization

The default optimization objective is:

```text
high predicted antimicrobial activity
+ low predicted mammalian toxicity
+ low predicted hemolysis
+ novelty
+ synthesis feasibility
+ diversity
```

Agents must not create objectives that optimize for:

* mammalian toxicity;
* delivery of harmful biological agents;
* increased virulence;
* immune evasion;
* pathogen enhancement;
* harmful host targeting;
* misuse against humans, animals, or crops.

## 5. No dangerous operational content

The repo must not include:

* wet-lab protocols for dangerous organisms;
* instructions for culturing or enhancing pathogens;
* instructions for misuse;
* toxin-design workflows;
* harmful objective functions;
* unscreened high-risk candidate releases;
* dangerous pathogen-specific optimization.

The project is dry-lab and safety-constrained unless a qualified human governance process explicitly approves the next step.

## 6. Reproducibility over impressiveness

A boring result that reproduces is better than an impressive result that cannot be checked.

Every major pipeline output must include:

* input data hash;
* model version;
* config file;
* command used;
* timestamp;
* random seed;
* code commit;
* output hash.

## 7. Benchmarks must be adversarial

Agents must actively search for ways the pipeline may be fooling itself:

* train/test leakage;
* near-duplicate contamination;
* bad negative datasets;
* overfitting to charge/hydrophobicity;
* memorization of known AMP motifs;
* inflated metrics;
* unstable rankings;
* toxicity blind spots.

If the result is easy to attack, fix the pipeline before claiming progress.

## 7.5. No simulation theater

Agents must not present speculative modeling layers as if they were validated assay surrogates.

If a membrane model, structure proxy, or learned emulator is added, agents must clearly state:

* what it actually models;
* what evidence supports it;
* where calibration data came from;
* what failure modes remain;
* whether it has shown better triage performance than simpler baselines.

An impressive-looking simulator that does not improve real decision quality is noise, not progress.

## 8. Human review is mandatory

AI agents may propose, implement, score, rank, and report.

AI agents may not make final scientific, safety, legal, or release decisions.

Human review is required before:

* publishing candidate sequences;
* contacting labs;
* releasing generator weights;
* changing safety policy;
* making external scientific claims;
* submitting a paper or press release.

---

# Agent Task Priorities

Agents should work in this order.

## Priority 1 — Make the pipeline real

Build and maintain:

* clean CLI;
* deterministic demo pipeline;
* candidate scoring;
* evidence certificate generation;
* schema validation;
* tests;
* CI;
* documentation.

## Priority 2 — Make benchmarks honest

Build:

* leakage checks;
* cluster splits;
* time splits where possible;
* negative-dataset comparisons;
* baseline models;
* ablation tests;
* reproducibility reports.

## Priority 3 — Make candidate selection defensible

Build:

* multi-model scoring;
* novelty analysis;
* toxicity penalty;
* diversity selection;
* synthesis feasibility filters;
* failure-mode reports;
* pre-registered selection rules.

## Priority 4 — Build the wet-lab compression roadmap

Build:

* virtual assay design docs;
* membrane interaction proxy modules;
* calibration datasets and benchmark scaffolding;
* uncertainty-aware surrogate models;
* active-learning candidate selection logic;
* evaluation against “cheap predictor only” baselines.

Do not oversell these modules before they are benchmarked honestly.

## Priority 5 — Make outputs scientifically reviewable

Build:

* candidate evidence JSON;
* batch reports;
* benchmark cards;
* model cards;
* dataset cards;
* safety review templates;
* release decision logs.

## Priority 6 — Prepare for external validation

Prepare:

* candidate batch pack;
* expert review pack;
* CRO/lab inquiry pack;
* pre-registered pass/fail criteria;
* independent replication plan;
* publication-quality methods description.

## Priority 7 — Learn from reality

After qualified assay data exists, build:

* lab-result ingestion;
* hit/failure calibration;
* retrospective analysis of why the model was right or wrong;
* updated selection policies that improve efficiency without changing success definitions after the fact.

---

# Non-Negotiable Kill Criteria

Stop or downgrade the project if any of the following occurs:

| Failure                                          | Required action                      |
| ------------------------------------------------ | ------------------------------------ |
| Pipeline cannot beat simple baselines            | Do not proceed to lab                |
| Ranking depends on data leakage                  | Fix benchmark before continuing      |
| Top candidates are near-duplicates of known AMPs | Strengthen novelty filter            |
| Toxicity risk is ignored                         | Block candidate release              |
| Results cannot be reproduced                     | Block external claims                |
| Agents propose dangerous objectives              | Remove and safety-review             |
| Human reviewer cannot understand evidence        | Improve reports before proceeding    |
| Lab results show no signal after repeated cycles | Publish negative result and reassess |

Failure is allowed.

Unverifiable success is not.

---

# Public Claim Policy

Allowed claims:

* “Computationally nominated candidate.”
* “Predicted antimicrobial peptide.”
* “Dry-lab candidate.”
* “Selected by reproducible pipeline.”
* “Experimentally tested candidate.”
* “Independently reproduced activity,” if true.
* “Novel candidate family,” if novelty analysis supports it.

Forbidden claims unless fully proven:

* “AI discovered an antibiotic.”
* “Drug candidate.”
* “Safe.”
* “Effective in humans.”
* “Clinically useful.”
* “Cure.”
* “Breakthrough therapy.”
* “Proven antimicrobial,” before lab validation.
* “World-first,” unless independently verified.

---

# The Final Desired Headline

The desired headline is not hype.

The desired headline is:

> **Open AI pipeline discovers a new antimicrobial peptide family, independently validated in lab tests, with full reproducible evidence trail released for scientific review.**

That is the result agents should work toward.

Everything else is noise.

---

# One-Sentence Mission

> **Build the world’s most rigorous open, safety-first AI antimicrobial peptide foundry: a system that generates, filters, documents, and experimentally validates novel antimicrobial candidates through reproducible evidence rather than hype.**
