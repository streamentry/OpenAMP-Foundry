# Goals

## North-star goal

**By the mid-2030s, OpenAMP Foundry should become the trusted open infrastructure for antimicrobial peptide experiment selection: a system independent labs can use to choose fewer, smarter, safer experiments and produce auditable evidence from every result.**

This is a goal, not a claim.

OpenAMP earns it only if it repeatedly beats cheap baselines in real experimental settings while preserving safety, reproducibility, and scientific honesty.

## The three outcomes that matter

The project has many useful sub-goals, but only three outcomes justify the long-term vision.

### 1. Experimental compression

OpenAMP should reduce the number of wet-lab experiments needed to find a useful antimicrobial signal.

A useful signal must not be defined after the fact. It must be pre-registered before a batch is tested.

The system should be judged against simple alternatives:

- random valid candidates;
- charge-density ranking;
- similarity to known AMPs;
- simple physicochemical heuristics;
- human expert selection where available;
- external predictor consensus.

If OpenAMP cannot beat these under fair comparison, the project must say so.

### 2. Safety-adjusted discovery

OpenAMP should not merely find candidates that look active.

It should improve the chance of finding candidates that are worth follow-up after considering predicted safety, hemolysis risk, cytotoxicity risk, novelty, synthesis feasibility, and redundancy.

A hit that is predictably unsafe or a near-duplicate is not the same as a discovery.

### 3. Auditable learning

Every experimental round should make the next round smarter or make the project more honest about why it cannot.

The project should preserve:

- what was selected;
- why it was selected;
- what baselines it beat;
- what controls were included;
- what failed;
- what changed after the result;
- what must not be claimed.

A discovery system that cannot explain its past decisions cannot become infrastructure.

## Goal hierarchy

```text
North star
  -> reduce wasted wet-lab search in antimicrobial peptide discovery
     -> through open, auditable candidate selection
        -> validated by independent assays
           -> compared against cheap baselines
              -> updated through controlled calibration
                 -> governed by safety-first release rules
```

## Phase 0 — Keep the foundation honest

**Status:** current dry-lab foundation.

The goal of Phase 0 is not to discover a drug. It is to make the computational substrate clean enough that real scientists can decide whether to spend lab budget on it.

### Required capabilities

- A clean checkout runs the demo pipeline.
- Candidate ranking is deterministic from fixed inputs.
- Evidence certificates validate against schemas.
- Benchmark reports are reproducible.
- Novelty checks are explicit.
- Safety-risk scores penalize rather than optimize harmful traits.
- Candidate diversity is part of selection.
- Known benchmark weaknesses are documented.
- Simulation modules cannot affect ranking until they beat baselines.
- The repo ships safe defaults and avoids unsafe wet-lab instructions.

### Phase 0 exit criteria

Phase 0 is complete only when a qualified external reviewer can inspect the project and answer “yes” to these questions:

1. Can I rerun the same candidate-selection process?
2. Can I see why each candidate was selected?
3. Can I see which cheap baselines were tested?
4. Can I see the safety boundaries?
5. Can I tell which claims are not yet supported?
6. Can I reject a candidate without relying on the maintainers’ confidence?

## Phase 1 — First wet-lab truth

**Target horizon:** first serious pilot.

The first real test is not whether the project can produce attractive candidates. It already can.

The first real test is whether its selection logic survives contact with independent wet-lab evidence.

### Required design

The first pilot should be pre-registered before candidate selection is finalized.

It should include:

- a small OpenAMP-selected candidate panel;
- positive and negative controls selected by qualified reviewers;
- cheap-baseline candidate panels for comparison;
- predefined activity and safety endpoints;
- predefined success and failure thresholds;
- candidate evidence certificates frozen before testing;
- a result-intake artifact that records outcomes without rewriting the selection story.

The project should not publish unsafe operational details. It should publish enough scientific metadata for reproducibility, review, and honest interpretation.

### Phase 1 success criteria

The first pilot is successful if it produces a clean answer to one of these questions:

1. OpenAMP selected candidates that are experimentally more useful than cheap baselines.
2. OpenAMP did not beat cheap baselines, but the failure mode is clear enough to improve the next batch.
3. OpenAMP’s current dry-lab assumptions are not useful enough for wet-lab spending and should be narrowed or redesigned.

A negative pilot can be a success if it is decisive.

An ambiguous pilot is not enough.

### Phase 1 failure criteria

Phase 1 fails if:

- success thresholds are changed after seeing results;
- failed candidates disappear;
- claims exceed the assay evidence;
- safety concerns are minimized to preserve the narrative;
- the OpenAMP panel is not compared against cheap baselines;
- the result cannot be independently interpreted.

## Phase 2 — Prove experimental compression

**Target horizon:** repeated pilots across multiple candidate-selection rounds.

The project becomes scientifically serious only after more than one experimental cycle.

The key question is:

> Does learning from real results improve future experiment selection?

### Required capabilities

- Batch-1 result intake through versioned schemas.
- Pre-registered recalibration gate.
- Human-reviewed model or weight updates.
- Batch-2 selection that includes both likely winners and information-rich uncertainty probes.
- Baseline comparison repeated after recalibration.
- Negative-result archive where safe.
- Public summary that distinguishes computational prediction from biological evidence.

### Phase 2 quantitative targets

These are targets, not claims.

OpenAMP should aim to show at least one of the following across repeated pilots:

| Target | Minimum evidence |
|---|---|
| Hit-rate improvement | OpenAMP-selected panels produce materially more useful activity signals than cheap-baseline panels under matched testing conditions. |
| Safety-adjusted yield | OpenAMP produces more follow-up-worthy candidates after accounting for activity, hemolysis/cytotoxicity risk, novelty, and redundancy. |
| Learning effect | Later batches outperform earlier batches in a way plausibly attributable to result-driven calibration, not cherry-picking. |
| Cost compression | The number of candidates needed to find a useful signal falls meaningfully versus baseline selection. |
| Transfer | The selection framework works across more than one AMP subfamily or benchmark split without silently retuning thresholds. |

The project should prefer conservative, boring evidence over dramatic weak evidence.

### Phase 2 kill rule

If repeated pilots show that OpenAMP does not beat cheap baselines after fair comparison, the project should stop claiming discovery leverage.

It may remain useful as:

- an educational pipeline;
- a reproducibility framework;
- a data-standard project;
- a negative-result archive;
- an audit system for candidate-selection claims.

But it should not call itself an experiment-compression engine until the evidence returns.

## Phase 3 — Become reusable infrastructure

**Target horizon:** after at least one credible wet-lab feedback loop.

At this stage the project should shift from “our pipeline” to “a shared substrate others can extend.”

### Infrastructure goals

- Stable evidence-certificate schema.
- Stable lab-result intake schema.
- Stable candidate-panel manifest format.
- Stable adapter API for external predictors and simulations.
- Benchmark registry with leakage checks.
- Safe negative-result archive format.
- Result-card format for human reviewers.
- Recalibration policy format.
- Release policy for safety-sensitive components.
- Long-term compatibility guarantees for core artifacts.

### Ecosystem goals

OpenAMP should make it easy for others to contribute without lowering scientific standards.

The project should support:

- independent predictor adapters;
- independent benchmark datasets;
- independent lab-result packages;
- independent scoring modules;
- independent safety-review improvements;
- independent candidate-panel strategies;
- external replications;
- adversarial benchmark audits.

Every extension should be judged by whether it improves decision quality, reproducibility, or safety.

## Phase 4 — Multi-lab validation

**Target horizon:** when the project has enough process maturity to support external use.

OpenAMP should not become dependent on one lab, one assay context, one maintainer, one dataset, or one model.

### Required evidence

Before claiming platform-level credibility, the project should have:

- multiple independent groups running the pipeline;
- more than one wet-lab partner or validation source;
- repeated baseline comparisons;
- documented failures from different contexts;
- at least one external replication of a meaningful result;
- public artifacts that allow reviewers to reconstruct the selection process;
- a governance process for safety-sensitive decisions.

### What “multi-lab” does not mean

It does not mean every lab gets the same result.

Biology is noisy. Context matters.

Multi-lab credibility means the project can preserve enough context, controls, and evidence for disagreement to be scientifically useful rather than confusing.

## Phase 5 — The biotech infrastructure ambition

**Target horizon:** decade-scale.

If OpenAMP succeeds in AMPs, it may generalize into a broader open infrastructure pattern for biology:

```text
hypothesis generation
  -> candidate triage
  -> evidence certificate
  -> qualified experimental test
  -> result intake
  -> calibration gate
  -> next experiment
  -> shared benchmark memory
```

The expansion path should be conservative.

OpenAMP should not jump into new biological domains because the narrative sounds bigger. It should expand only when the same evidence discipline can be maintained.

Possible future extensions include:

- other peptide discovery tasks;
- selectivity and toxicity benchmarking;
- stability and manufacturability modeling;
- assay-result standards;
- open experimental-design tooling;
- safe active-learning infrastructure for constrained biological systems.

The long-term win is not owning all biology.

The win is creating a trusted open pattern for connecting AI systems to experimental evidence.

## Annual strategic goals

### Goal A — Make every claim auditable

Every important output should link to:

- input files;
- config files;
- code version;
- random seed where relevant;
- benchmark result;
- candidate evidence;
- safety flags;
- known limitations;
- reviewer decision if applicable.

No major claim should depend on maintainer confidence.

### Goal B — Attack the easiest explanation first

Before accepting an advanced model improvement, test whether the result is explained by:

- charge;
- length;
- hydrophobicity;
- similarity to known AMPs;
- benchmark leakage;
- duplicate families;
- data-source artifacts;
- post-hoc threshold changes;
- selection bias;
- missing safety penalties.

Only the residual signal matters.

### Goal C — Turn failures into assets

A failed candidate can still improve the system if it is recorded safely and interpreted honestly.

The project should build infrastructure where negative results are first-class evidence rather than reputational damage.

### Goal D — Make safety a design constraint

Safety should not be a disclaimer at the end.

It should affect defaults, objectives, release policy, docs, candidate publication, adapter behavior, and review gates.

### Goal E — Make the project useful to serious outsiders

A serious external user should be able to:

- run the pipeline;
- inspect the scoring logic;
- plug in a predictor;
- add a benchmark;
- validate an evidence certificate;
- prepare a safe lab handoff;
- ingest results;
- reproduce a recalibration decision;
- disagree with the model using evidence.

## Metrics dashboard

The project should maintain a dashboard of metrics that cannot be gamed easily.

### Dry-lab metrics

- Pipeline AUROC/AUPRC on frozen benchmarks.
- Performance against charge-matched and similarity-controlled baselines.
- Cross-dataset generalization.
- Per-family performance.
- Top-k precision and recall.
- Novelty audit quality.
- Candidate diversity.
- Safety-risk distribution.
- Evidence-certificate validity rate.
- CI test count and coverage where useful.

### Wet-lab-facing metrics

- Number of pre-registered pilots.
- Number of candidates tested through qualified partners.
- Number of safe, interpretable negative results.
- Hit-rate versus cheap baselines.
- Safety-adjusted yield versus cheap baselines.
- Replication rate.
- Cost per useful signal.
- Time from result intake to next pre-registered batch.
- Number of calibration updates rejected by gate.

### Ecosystem metrics

- Independent contributors.
- External predictor adapters.
- External benchmark contributions.
- External lab-result packages.
- Independent reruns.
- Independent critiques resolved.
- Downstream projects using evidence-certificate or result schemas.

Stars are weak evidence.

External reproducible use is strong evidence.

## Red flags

The project is drifting if any of these happen:

- README claims become stronger than evidence.
- A model affects ranking without beating cheap baselines.
- Candidate novelty is asserted without serious reference comparison.
- Safety scores become marketing rather than gates.
- Results are summarized without controls.
- Negative outcomes are hidden or under-documented.
- Wet-lab language implies clinical or therapeutic value.
- Benchmarks improve after threshold changes that were not pre-registered.
- External users cannot reproduce core artifacts.
- The project starts optimizing for attention instead of trust.

## Non-goals

OpenAMP Foundry is not trying to be:

- a clinical drug-development company;
- a medical advice system;
- a pathogen-engineering tool;
- a wet-lab protocol repository;
- a toxin-design system;
- a black-box SaaS ranking oracle;
- a benchmark-gaming leaderboard;
- a candidate dump;
- a replacement for qualified microbiologists, toxicologists, clinicians, regulatory experts, or safety reviewers.

## Claim ladder

The project should use stricter language as evidence improves.

| Evidence level | Allowed claim |
|---|---|
| Dry-lab score only | “Computationally nominated candidate.” |
| Passed novelty/safety/ranking gates | “Candidate selected for qualified review.” |
| Approved for pilot | “Candidate selected for experimental testing under pre-registered criteria.” |
| Initial assay signal | “Candidate showed activity under specific test conditions.” |
| Safety-screened initial signal | “Candidate showed an activity/safety profile worth follow-up under specific test conditions.” |
| Independent replication | “Candidate family has externally replicated early antimicrobial evidence.” |
| Much later translational work | Only qualified domain experts may decide stronger claims. |

The default public claim should be weaker than the maintainer wants.

## Governance goals

As the project grows, governance must become explicit.

Required governance areas:

- maintainer roles;
- benchmark-change review;
- safety-sensitive release review;
- model-weight release policy;
- candidate-publication policy;
- external lab-result acceptance criteria;
- conflict-of-interest disclosure;
- contributor code of scientific conduct;
- deprecation policy for misleading modules;
- emergency rollback path for unsafe content.

Open infrastructure without governance becomes fragile infrastructure.

## The cheapest disconfirming tests

The project should constantly run tests that could prove its own story wrong.

### Test 1 — Charge-only challenger

Can the full system beat a charge-density or charge-aware baseline on realistic candidate selection?

### Test 2 — Similarity challenger

Can the system find candidates that are not merely near-neighbors of known AMPs?

### Test 3 — Safety challenger

Does the ranking avoid candidates that look active only because they are broadly membrane-disruptive or likely unsafe?

### Test 4 — Wet-lab challenger

Do top-ranked candidates produce more useful experimental outcomes than baseline panels?

### Test 5 — Learning challenger

Does batch 2 improve because of batch 1 results?

### Test 6 — External-user challenger

Can a serious external group reproduce the pipeline and understand the evidence without private maintainer context?

If these tests fail, the project should change direction.

## Definition of “insanely great”

OpenAMP Foundry is not insanely great when it produces a beautiful demo.

It is insanely great when it makes a serious scientist more willing to trust an open workflow than a private black box.

It is insanely great when a failed batch still improves the shared knowledge base.

It is insanely great when an external lab can reconstruct why every candidate was tested.

It is insanely great when cheap baselines are treated as enemies, not ignored.

It is insanely great when safety slows the project down in the right places.

It is insanely great when the software becomes boring enough that the science can be judged clearly.

## Final goal

The final goal is not to make OpenAMP famous.

The final goal is to make antimicrobial discovery more trustworthy, more open, more reproducible, and more experimentally efficient.

If the project earns that role over years, then it can become part of the open base layer for biotech.

That is the only version of the “Linux for biology” ambition worth taking seriously.
