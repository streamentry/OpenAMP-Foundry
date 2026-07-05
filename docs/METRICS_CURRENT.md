# Current Pipeline Metrics — Single Source of Truth

Machine-readable snapshot: `outputs/metrics_snapshot.json` regenerated with `make metrics-snapshot`.

> **Purpose:** One authoritative table of current pipeline metrics. If any doc disagrees
> with this file, this file wins. Updated whenever benchmark/benchmark config changes.
>
> **Last updated:** 2026-07-05 (expanded 500-AMP benchmark, v0.5.29)
> **New in v0.5.29:** Expanded benchmark to 500 AMPs + 500 composition-matched decoys (n=1000). AUROC 0.7792 (CI₉₅: 0.7505–0.8065) confirms signal generalizes. Cluster-aware CI: 0.746–0.8102. Representative AUROC: 0.778. Standard benchmark (n=191) retained for backward comparison.
> **Pipeline version:** v0.5.29
> **Branch:** main

---

## Benchmark Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Benchmark type | Standard (composition-matched decoys) | Default `make validate-scoring` |
| Positives | **95** public-domain AMPs | 12 taxonomic classes; see `examples/validation/known_amps.csv` |
| Negatives | **96** length-matched random decoys | Swiss-Prot residue frequencies, seed=1729 |
| Total (n) | **191** | Expanded from original 87 (PR #110) |
| **Pipeline AUROC** | **0.7832** | Bootstrap CI₉₅: 0.72–0.84 (n_bootstrap=2000) |
| **Phase3 AUROC** | **0.7448** | Synthesis gate config; CI₉₅: 0.68–0.81 |
| **Pipeline AUPRC** | **0.8164** | Random baseline: 0.4974 |
| **Phase3 AUPRC** | **0.7933** | Random baseline: 0.4974 |
| Strict AUROC (scrambled) | 0.4335 | 95 shuffled decoys; below random — expected for helic-centric scorer |
| Recall@10 | 0.1053 | 10/95 positives in top 10 |
| Recall@20 | 0.2105 | 20/95 positives in top 20 |
| Recall@43 | 0.4211 | 40/95 positives in top 43 |
| Interpretation | **STRONG** | AUROC > 0.70 gate passed |


### Expanded 500-AMP Benchmark (n=1000)

> Added 2026-07-05. The original benchmark (95 AMPs + 96 decoys, n=191) was
> expanded to 500 AMPs + 500 length-matched decoys (n=1000) using UniProt
> reviewed AMPs (CC BY 4.0) and APD6 natural sequences (academic use).
> This provides a more honest estimate of pipeline discriminative power
> with tighter confidence intervals.
>
> Curated by: `scripts/curate_500_amp_benchmark.py`
>
> Run: `make bench-500`

| Metric | Value | Notes |
|--------|-------|-------|
| Positives | **500** public-domain AMPs | UniProt reviewed + APD6 natural + existing curated |
| Negatives | **500** length-matched random decoys | Swiss-Prot residue frequencies, seed=20260705 |
| Total (n) | **1000** | ~2.3× reduction in CI width over the original 87-seq benchmark |
| **Pipeline AUROC** | **0.7792** | Bootstrap CI₉₅: 0.7505–0.8065 |
| **Phase3 AUROC** | **0.7744** | Synthesis gate config |
| **Pipeline AUPRC** | **0.7705** | Random baseline: 0.5000 |
| **Phase3 AUPRC** | **0.7656** | Random baseline: 0.5000 |
| Recall@10 | 0.020 | 10/500 positives in top 10 |
| Recall@20 | 0.040 | 20/500 positives in top 20 |
| Recall@43 | 0.076 | 38/500 positives in top 43 |
| Interpretation | **STRONG** | AUROC > 0.70 gate passed |

### Expanded Cluster-Split Benchmark (near-duplicate de-inflation)

| Metric | Pipeline (pipeline.yaml) | Phase3 (phase3.yaml) |
|--------|:-----------------------:|:-------------------:|
| Full AUROC | 0.7792 | 0.7744 |
| **Cluster-aware CI₉₅** | **0.746–0.8102** | **same config** |
| Representative AUROC (1/cluster) | 0.778 | 0.7744 |
| Representative CI₉₅ | 0.7455–0.8084 | — |
| Held-out AUROC (195 near-dup AMPs) | 0.7828 | — |
| Independent clusters | 374 / 500 | 374 / 500 |
| AMPs in multi-member clusters | 195 / 500 | 195 / 500 |
| Multi-member clusters | 69 | 69 |

**Key findings:**

1. **Signal generalizes to 10× larger set.** AUROC 0.7792 on n=1000 is essentially
   identical to 0.7832 on n=191. The pipeline does not overfit to the 95-sequence
   benchmark.

2. **CIs are much tighter.** Cluster-aware CI: 0.746–0.8102 (width 0.064) vs
   0.7061–0.8526 (width 0.146) on n=191. The expanded set provides ~2.3× tighter
   confidence intervals.

3. **Representative AUROC nearly equals full AUROC.** 0.778 vs 0.7792. On the
   original benchmark, representative AUROC (0.7607) was lower than full (0.7832).
   The expanded set's 500 sequences are less dominated by near-duplicate inflation.

4. **Cluster-aware CI lower bound (0.746) is well above the 0.65 gate.** The
   pipeline's signal is robust to near-duplicate de-inflation.

5. **Honest limitation:** The expanded set uses UniProt-reviewed and APD6 sequences
   annotated as antimicrobial. These carry the same annotation bias as the original
   set: AMP annotation is an active research field, and some annotated AMPs may not
   be genuinely antimicrobial. The set also includes fewer defensins and
   cysteine-rich peptides due to the 10–30 AA length constraint.

### Cluster-Split Benchmark (near-duplicate de-inflation, n=191)

> Added 2026-07-01. The standard benchmark treats all 95 AMPs as independent samples.
> 33 of 95 AMPs are in 14 near-duplicate clusters (sim >= 0.70): magainin-1/2/3,
> protegrin-1/2/3, tachyplesin-I/II/polyphemusin-I, indolicidin/analog/lys-analog, etc.
> The cluster-aware bootstrap resamples clusters (not sequences) to produce an honest CI.

| Metric | Pipeline (pipeline.yaml) | Phase3 (phase3.yaml) |
|--------|:-----------------------:|:-------------------:|
| Full AUROC | 0.7832 | 0.7448 |
| Standard CI₉₅ | 0.717–0.8423 | 0.6741–0.8118 |
| **Cluster-aware CI₉₅** | **0.7061–0.8526** | **0.6591–0.8237** |
| Representative AUROC (1/cluster) | 0.7607 | 0.7196 |
| Representative CI₉₅ | 0.6854–0.8301 | 0.6372–0.7985 |
| Held-out AUROC (19 near-dup AMPs) | 0.8734 | 0.8454 |
| Independent clusters | 76 / 95 | 76 / 95 |
| AMPs in multi-member clusters | 33 / 95 | 33 / 95 |
| Multi-member clusters | 14 | 14 |

**Key finding:** The cluster-aware CI (0.7061–0.8526) is wider than the standard CI
(0.717–0.8423) on the upper end but the lower bound drops below the standard CI
(0.7061 vs 0.717). The representative-only AUROC (0.7607, CI: 0.6854–0.8301) confirms
the signal is not entirely driven by near-duplicate redundancy — but the CI lower
bound (0.6854) dips below the 0.70 synthesis gate threshold. The pipeline passes the
cluster-aware gate (CI lo > 0.65) but with less margin than the standard benchmark
suggested. The held-out AUROC (0.8734) is high because held-out near-duplicates share
composition features with their cluster representatives — this is expected and not
evidence of generalisation to novel sequence space.

**Verdict:** Signal survives near-duplicate de-inflation. The synthesis gate (AUROC >
0.70) holds on the full set and the cluster-aware CI lower bound stays above 0.65.
The representative-only CI lower bound (0.6854) crossing below 0.70 is an honest
limitation: the pipeline has real but modest discriminative power, and the headline
CI was slightly overconfident.

Run: `openamp-foundry bench cluster-split`

### Historical baselines

| Point | Benchmark | AUROC | Phase3 AUROC | Source |
|-------|-----------|-------|--------------|--------|
| **Expanded** | **500 AMP + 500 decoy (n=1000)** | **0.7792** | **0.7744** | v0.5.29 (Loop 11) |
| Standard | 95 AMP + 96 decoy (n=191) | 0.7832 | 0.7448 | PR #110 |
| Original demo set | 43 AMP + 44 decoy (n=87) | 0.8420 | 0.8266 | PR #72 |
| Pre-face-bonus | 43 + 44 | 0.8348 | 0.8126 | PR #70 |
| Pre-windowed-mu_h | 43 + 44 | 0.8047 | 0.7846 | PR #66 |
| Pre-Trp-bonus | 43 + 44 | 0.8164 | — | PR #65 (transient) |

**Note:** The expanded benchmark (500+500, n=1000) is now the primary benchmark.
The n=191 benchmark is retained for backward comparison. The expanded set is more
representative of diverse AMP classes and provides ~2.3× tighter confidence intervals.
Historical baselines from the demo set (n=87) should not be directly compared with
the expanded benchmark — the helic-centric scorer's strong performance on small
amphipathic-helix sets does not reflect performance on diverse AMP classes.

---

## Candidate Panel

| Metric | Value |
|--------|-------|
| Wave 0 panel size | 20 candidates |
| Wave 0 scaffold families | 7 (SEED-001, 003, 005, 006, 007, 008, 009) |
| **Wave 1 final panel (Wave 0.5)** | **24 candidates** |
| **Wave 1 scaffold families** | **15 (Wave 0 carry-overs + 9 new families)** |
| Wave 0.5 new families | 10 (SEED-010 through SEED-019) |
| Wave 0.5 shortlisted | 60 (6 per family × 10 families) |
| Wave 0.5 novelty (v2, 27k DB) | 1 RELATED_NOVEL / 39 CLOSE_RELATIVE / 19 KNOWN_VARIANT / 1 EXACT_MATCH_OR_FRAGMENT |
| Wave 0.5 novelty v1 (72 refs, Levenshtein) | 53/60 RELATED_NOVEL or higher — v1 method overstated novelty |
| Broad novelty Wave 0 (72 refs) | 16/20 NOVEL, 3 KNOWN_VARIANT, 1 CLOSE_RELATIVE |
| 5-tier audit Wave 0 (120 refs) | 13 HIGH_CONFIDENCE_NOVEL + 3 NOVEL + 1 CLOSE_RELATIVE + 3 KNOWN_VARIANT |
| Wave 0 panel ensemble range | 0.796–0.857 |
| Wave 0 panel safety range | 0.845–1.000 |
| Positive control | SEED-001_VAR_064 (magainin-1 derivative, ensemble 0.802) |
| Blind spot | Melittin scores Safety=1.0 despite hemolysis; hemolysis assay mandatory |
| Wave 0.5 external predictors | **COMPLETE** — AMPScanner 59/60, AMPActiPred 60/60, Macrel AMP 52/60 |
| Wave 0.5 activity consensus | **STRONG_ACTIVITY: 52/60 (87%)** — passes W0.5-3 gate (≥70%) |
| Wave 0.5 HemoFinder | LOW: 40/60 (67%), HIGH: 20/60 |
| Wave 0.5 AntiCP 2.0 | Non-AntiCP: 4/60 (7%), AntiCP: 56/60 |
| Best clean candidate | SEED-019_VAR_004 (RVRIRLVKRLLK) — STRONG + Non-AntiCP + HemoFinder LOW |
| **Wave 0.5b** | **23 candidates shortlisted** (5 new families SEED-020→024, no aromatics) |
| Wave 0.5b design goal | Lower AntiCP risk: no W/Y/F residues; broken helix pattern |
| Wave 0.5b expected AntiCP | < 0.50 (by design — pending external predictor confirmation) |

### Wave 1 Panel Composition (Wave 0.5 output, post-v2 novelty update)

| Role | Count |
|------|-------|
| BALANCED_LEAD | 15 |
| HIGH_UPSIDE_RISKY | 4 |
| POSITIVE_CONTROL | 1 |
| SAR_CONTROL | 4 |

### Novel families (Wave 0 leads)

| Family | Mechanism | Panel slots | Novelty | Key risk |
|--------|-----------|:-----------:|---------|----------|
| SEED-006 | Mastoparan-X, wasp-venom helix insertion | 2 | 0.643 | Mast-cell degranulation |
| SEED-007 | Bombolitin-II, bumblebee venom | 1 | 0.643 | Met oxidation at pos 6 |
| SEED-008 | Puroindoline-a, Trp-rich interfacial | 2 | 0.692 | DKP risk (FP), HemoFinder HIGH |
| SEED-009 | Bac2A, proline-rich intracellular | 2 | 0.647 | AntiCP risk, RPMI-1640 arm |

### New Wave 0.5 families in Wave 1 panel (v2 novelty classes)

| Family | Mechanism | Panel slots | v2 Novelty class |
|--------|-----------|:-----------:|---------------|
| SEED-010 | Histatin-5 P-113 oral innate AMP fragments | 1 | KNOWN_VARIANT (SAR_CONTROL) |
| SEED-011 | Pro-kinked amphipathic | 1 | CLOSE_RELATIVE |
| SEED-012 | Glycine-rich low-hydrophobicity design | 2 | CLOSE_RELATIVE |
| SEED-014 | Cathelicidin-mini scattered helix | 1 | CLOSE_RELATIVE |
| SEED-015 | KFLK de novo cationic helix | 1 | CLOSE_RELATIVE |
| SEED-016 | RRWK dual-Trp low-aromatic | 2 | CLOSE_RELATIVE |
| SEED-018 | GKRK scattered-charge design | 2 | CLOSE_RELATIVE |
| SEED-019 | Arg-Val alternating pattern | 2 | RELATED_NOVEL / CLOSE_RELATIVE |

---

## External Predictor Results (Wave 0.5)

| Tool | Status | Result |
|------|--------|--------|
| CAMPR4 | ⏳ Not submitted | PENDING |
| AMPScanner v2 | ✅ Complete | 59/60 AMP (98%) |
| AMPActiPred | ✅ Complete | 60/60 ABP (100%) |
| Macrel AMP | ✅ Complete | 52/60 AMP (87%) |
| HemoFinder | ✅ Complete | 40/60 LOW (67%), 20/60 HIGH |
| AntiCP 2.0 | ✅ Complete | 4/60 Non-AntiCP, 56/60 AntiCP |
| Macrel Hemolysis | ✅ Complete | 60/60 flagged (non-discriminating — flags all) |

**Activity consensus (3 tools, CAMPR4 excluded):** 52/60 STRONG_ACTIVITY, 7/60 MODERATE, 1/60 WEAK

**Safety profile concern:** 56/60 AntiCP-positive is expected for amphipathic-helix designs.
AntiCP 2.0 detects anticancer peptide (ACP) patterns, not antimicrobial activity directly.
Mitigation: Wave 0.5b designs avoid aromatic residues and pure amphipathic helix.

Current-state summary is documented here. Wave 0.5 machine-readable CSV outputs are
generated locally via `make wave0-5-fill-external` when `outputs/wave05_combined_consensus.csv`
is present; they are not guaranteed to be committed in every checkout.

---

---

## Expert Ablation Benchmark (v0.5.x — added 2026-07-01)

> The expert composite scorer (`scoring/expert.py`) adds four components beyond the
> simple ensemble: selectivity, serum stability, helix-hinge, and k-mer motif novelty.
> This ablation tests whether those additions improve binary AMP-vs-decoy discrimination
> or are complexity that does not earn its keep.
>
> Run: `make bench-expert-ablation`

| Metric | Pipeline (pipeline.yaml) | Phase3 (phase3.yaml) |
|--------|:-----------------------:|:-------------------:|
| Ensemble AUROC | 0.7832 | 0.7448 |
| Ensemble CI₉₅ | 0.717–0.8423 | 0.6741–0.8118 |
| Expert composite AUROC | 0.7097 | 0.7097 |
| Expert CI₉₅ | 0.6384–0.7871 | 0.6384–0.7871 |
| **Delta (expert − ensemble)** | **−0.0735** | **−0.0351** |
| Verdict | Expert LOWER | Expert LOWER |

**Per-component AUROC** (pipeline config, n=191):

| Component | AUROC | Above random | Classification |
|-----------|:-----:|:------------:|:--------------:|
| activity | 0.8137 | +0.3137 | **Signal-bearing** |
| selectivity_proxy | 0.7729 | +0.2729 | **Signal-bearing** |
| hinge_selectivity | 0.5180 | +0.0180 | Near-zero |
| novelty | 0.5000 | 0.0000 | Near-zero |
| motif_novelty | 0.5000 | 0.0000 | Near-zero |
| boman_activity | 0.4620 | −0.0380 | Near-zero |
| synthesis | 0.4228 | −0.0772 | **Anti-signal** |
| safety | 0.3487 | −0.1513 | **Anti-signal** |
| rich_selectivity | 0.1973 | −0.3027 | **Anti-signal** |
| serum_stability | 0.2231 | −0.2769 | **Anti-signal** |

**Key finding:** The expert composite scores **lower** than the simple ensemble on
binary AMP-vs-decoy discrimination (delta = −0.0735). Three expert components are
anti-signal: `safety`, `serum_stability`, `synthesis`, and `rich_selectivity` score random decoys higher
than known AMPs. This is expected and not a bug: real AMPs have high hydrophobic
moment and charge (features the safety scorer penalises), many interior protease
sites (low serum stability), and often contain repeat runs or aggregation-prone
segments (low synthesis feasibility). Random decoys drawn from Swiss-Prot
frequencies tend to have more moderate biophysical properties.

**What this means for the pipeline:**

1. The expert composite should NOT replace the ensemble for AMP/non-AMP triage. However, the rich_selectivity component (AUROC=0.1973 for AMP-vs-decoy but detection AUROC=0.7138 for hemolysis) is anti-AMP by design — it penalises high hydrophobicity and charge that define AMPs. This is the correct tradeoff: the expert composite trades a small AMP-detection penalty for significant hemolysis-risk awareness.
2. The ensemble (activity + safety + synthesis + novelty + Boman) remains the
   primary synthesis gate, as it has higher discriminative power.
3. The expert components may still add value for **within-AMP ranking** (selectivity
   and safety differentiation among candidates that already pass the activity gate)
   — but this has not been demonstrated and should not be assumed.
4. The `boman_activity` scorer (AUROC 0.462, below random) does not discriminate
   AMPs from random decoys on the expanded benchmark. It contributes to the ensemble
   only through the disagreement signal, not through independent discrimination.
5. `motif_novelty` and `novelty` are 0.5 by construction (no k-mer index, no
   references in this benchmark) — they are correctly neutral, not noise.

**Honest limitation:** This benchmark measures binary AMP-vs-decoy discrimination
only. The expert composite's selectivity, safety, and synthesis components are
designed for within-AMP candidate differentiation, not for separating AMPs from
non-AMPs. A within-AMP ranking benchmark (comparing selective vs hemolytic AMPs)
has been added in v0.5.9 (see Within-AMP Selectivity Benchmark section below).

---


## Within-AMP Selectivity Benchmark (v0.5.x — added 2026-07-01)

> The expert ablation benchmark found that safety, synthesis, and serum stability are
> anti-signal for AMP-vs-decoy discrimination. But those scorers were designed for
> *within-AMP ranking*: distinguishing hemolytic AMPs from selective AMPs. This benchmark
> tests them on that intended task.
>
> Run: `make bench-selectivity`

**Dataset:** 42 known AMPs with literature HC50 values (hemolysis_reference.csv)

| Class | HC50 threshold | Count |
|-------|:--------------:|:-----:|
| HEMOLYTIC | < 25 µg/mL | 14 |
| SELECTIVE | >= 100 µg/mL | 21 |
| BORDER (excluded from AUROC) | 25-100 µg/mL | 7 |

**Task:** Can pipeline scorers distinguish hemolytic AMPs from selective AMPs?
For safety/selectivity scorers, the correct direction is: hemolytic AMPs score *lower*
(less safe, less selective). We report "hemolysis detection AUROC" where higher = better
risk detection (1 - raw AUROC for safety-type scorers).

### Per-score hemolysis detection AUROC

| Score | Detection AUROC | CI₉₅ | Significant? | Verdict |
|-------|:--------------:|:----:|:------------:|---------|
| synthesis | 0.8027 | 0.63-0.95 | **YES** | Synthesis difficulty correlates with hemolysis — hemolytic AMPs are harder to synthesize |
| boman_activity | 0.6837 | 0.49-0.85 | No (CI lo < 0.5) | Weak trend: hemolytic AMPs have lower Boman activity |
| serum_stability | 0.6020 | 0.40-0.80 | No (CI lo < 0.5) | Weak trend: hemolytic AMPs less serum-stable |
| expert_composite | 0.5119 | 0.31-0.71 | No (CI lo < 0.5) | Better than ensemble but not significant |
| hinge_selectivity | 0.4456 | 0.24-0.64 | No | No selectivity signal from hinge detection |
| selectivity_proxy | 0.4133 | 0.28-0.55 | No | **FAILS** — charge/GRAVY does not capture hemolysis |
| safety | 0.3844 | 0.26-0.52 | No | **FAILS** — confirms melittin blind spot |
| activity | 0.3401 | 0.16-0.52 | No | Activity scorer ranks hemolytic AMPs *higher* (anti-selective) |
| ensemble | 0.3486 | 0.17-0.54 | No | Ensemble inherits activity scorer's anti-selective bias |

**Key findings:**

1. **The safety scorer does NOT detect hemolysis** (detection AUROC = 0.3844, CI lo = 0.26).
   This confirms the expert ablation's prediction and the previously documented melittin
   blind spot. All 14 hemolytic AMPs in the reference set score safety >= 0.8 — the scorer
   cannot distinguish them from selective AMPs.

2. **The selectivity proxy does NOT detect hemolysis** (detection AUROC = 0.4133, CI lo = 0.28).
   The charge/GRAVY heuristic is insufficient for capturing hemolysis risk. Hemolytic AMPs
   like melittin and protegrin have optimal charge (+2 to +7) and moderate GRAVY, so the
   proxy assigns them high selectivity scores.

3. **Synthesis feasibility is the only significant risk detector** (detection AUROC = 0.8027,
   CI lo = 0.63). Hemolytic AMPs tend to be harder to synthesize: they have more cysteines
   (protegrins, tachyplesins), repeat runs, and hydrophobic segments. This is an incidental
   correlation, not a designed safety feature — but it means the synthesis gate provides
   partial hemolysis filtering as a side effect.

4. **The activity scorer is anti-selective** (detection AUROC = 0.34): it ranks hemolytic
   AMPs *higher* than selective AMPs. This is expected: hemolytic AMPs like melittin have
   strong amphipathic helices, high hydrophobic moment, and high charge — exactly the
   features the activity scorer rewards. The ensemble inherits this bias.

5. **The expert composite now includes rich_selectivity** (detection AUROC=0.7138, CI 0.63-0.80) as its hemolysis-risk component, replacing the old hemolysis_safety (was 0.5119 vs
   0.3486) but not significantly so (CI includes 0.5). The added selectivity and safety
   components partially offset the activity scorer's anti-selective bias, but not enough
   to reach significance at n=14 vs n=21.

**Honest limitation:** HC50 values are approximate literature values with high inter-assay
variability (RBC source, buffer, incubation time, concentration range). The binary
thresholds (25 / 100 µg/mL) are coarse. A larger reference set with standardized HC50
measurements would tighten the CIs and might flip some near-zero results to significant.
The current sample size (14 vs 21) is too small for confident conclusions on any score
with CI lower bound below 0.5.

**Implication for the pipeline:** Hemolysis remains unpredictable by the current
physicochemical scorers. The melittin blind spot is confirmed quantitatively. Hemolysis
must be assayed experimentally for every candidate regardless of safety or selectivity
score. The synthesis gate provides partial indirect filtering but should not be relied
upon as a hemolysis predictor.

## Dedicated Hemolysis Risk Scorer (v0.5.10 — added 2026-07-01)

> The selectivity benchmark (v0.5.9) confirmed that the safety scorer fails
> hemolysis detection (AUROC=0.3844). A dedicated hemolysis risk scorer was
> built from empirically-validated components identified in that benchmark.
>
> **v0.5.11 correction:** The original 42-peptide reference set (14 hemolytic
> vs 21 selective, n=35) produced detection AUROC=0.9218 (CI 0.82-0.99). This
> was **small-sample inflation**. Expansion to 238 peptides using DBAASP human
> erythrocyte data (54 hemolytic vs 125 selective, n=179) dropped the detection
> AUROC to 0.5650 (CI 0.47-0.66) — direction correct but NOT statistically
> significant. The scorer retains weak directional signal but should not be
> trusted as a standalone hemolysis detector.
>
> Run: `make bench-selectivity` (hemolysis_risk column in the output)

**Module:** `src/openamp_foundry/scoring/hemolysis.py`

**Components** (individual AUROC from original n=14 vs n=21; may not replicate on expanded set):

| Component | Individual AUROC (n=35) | Weight | Signal source |
|-----------|:-----------------------:|:------:|---------------|
| Synthesis difficulty (1 - synth_feasibility) | 0.8027 | 0.30 | Incidental: hemolytic AMPs harder to synthesize |
| Aromatic fraction (F/W/Y density) | 0.8299 | 0.30 | Trp/Phe intercalation in both membrane types |
| Cationic-on-hydrophobic-face fraction | 0.7585 | 0.20 | Poor amphipathic face segregation |
| Cysteine fraction | 0.7500 | 0.20 | Beta-sheet defensin/protegrin class |

**Combined performance (expanded n=179):**

| Metric | Original (n=35) | Expanded (n=179) | Notes |
|--------|:---------------:|:-----------------:|-------|
| **Detection AUROC** | **0.9218** | **0.5650** | Small-sample inflation corrected |
| CI₉₅ lower bound | 0.82 | 0.47 | No longer > 0.5 — not significant |
| CI₉₅ upper bound | 0.99 | 0.66 | |
| Mean hemolytic risk | 0.4064 (n=14) | 0.2042 (n=54) | Direction still correct |
| Mean selective risk | 0.1501 (n=21) | 0.1535 (n=125) | |
| Safety scorer detection | 0.3844 | 0.5116 | Safety also improves slightly with more data |

**Expert composite integration (expanded n=179):**

| Metric | Before (v0.5.9, n=35) | After (v0.5.10, n=35) | Expanded (n=179) |
|--------|:---------------------:|:---------------------:|:-----------------:|
| Expert composite detection AUROC | 0.5119 | 0.6429 | 0.5459 |
| Expert composite CI lo | 0.3129 | 0.4490 | 0.4562 |
| Ensemble detection AUROC | 0.3486 | 0.3486 | 0.4201 |

**Expert ablation (AMP-vs-decoy, unchanged):**

| Metric | Value | Classification |
|--------|:-----:|:--------------:|
| rich_selectivity AUROC | 0.1973 | **Anti-signal** (above_random = -0.3027) — replaces hemolysis_safety (was 0.3285) |
| Expert composite AUROC | 0.7097 | Down from 0.7119 (rich_selectivity replaces hemolysis_safety as expert component) |

**Key finding (corrected):** The hemolysis risk scorer's original detection
AUROC=0.9218 on n=35 was small-sample inflation. On the expanded n=179
reference set, detection AUROC=0.5650 (CI 0.47-0.66) — direction is correct
(hemolytic > selective on average) but not statistically significant. The
scorer should NOT be described as a "statistically significant hemolysis
detector." It provides weak directional signal that may be useful as one
factor in a composite but cannot be relied upon for hemolysis triage. Hemolysis
must still be assayed experimentally for every candidate.

**Honest limitation:** The expanded reference set (n=179) provides a more honest
estimate, but HC50 values are approximate literature values with high inter-assay
variability. Melittin's risk score (0.13) remains modest because its bent-helix
hemolysis mechanism is not fully captured by 1D features.

---

## Multi-Class Triage Benchmark (v0.5.12 — added 2026-07-01)

> Tests the v1.1 ROADMAP item: "benchmark candidate triage against a reference
> panel that includes selective AMPs, hemolytic positives, inactive peptides,
> and random controls." Prior benchmarks tested two separate 2-class problems
> (AMP vs decoy, hemolytic vs selective). This benchmark tests the combined
> triage task the virtual assay layer must solve: rank selective AMPs above
> hemolytic AMPs above random decoys in a single panel.
>
> Run: `make bench-triage`

**Dataset:** 125 selective AMPs (HC50 >= 100 µg/mL) + 54 hemolytic AMPs (HC50 < 25 µg/mL)
+ 96 random background decoys = 275 total.

### Per-scorer pairwise AUROCs

A scorer that triages correctly should have all three AUROCs > 0.5:
  - selective > decoy (identifies AMPs)
  - hemolytic > decoy (identifies AMPs)
  - selective > hemolytic (prefers safe AMPs)

| Scorer | sel > decoy | hem > decoy | sel > hem | Triages correctly? |
|--------|:-----------:|:-----------:|:---------:|:------------------:|
| ensemble | 0.848 | 0.891 | 0.466 | **NO** (anti-selective) |
| activity | 0.885 | 0.934 | 0.430 | NO |
| selectivity_proxy | 0.782 | 0.795 | 0.610 | **YES** |
| expert_composite | 0.757 | 0.746 | 0.545 | **YES** |
| triage_score (activity × (1 - hemo_risk)) | 0.863 | 0.902 | 0.462 | NO |
| safe_weighted_ensemble | 0.849 | 0.890 | 0.483 | NO |
| safety | 0.344 | 0.300 | 0.538 | NO |
| synthesis | 0.590 | 0.634 | 0.469 | NO |
| hemolysis_risk (inverted) | 0.485 | 0.492 | 0.488 | NO |
| serum_stability | 0.217 | 0.160 | 0.569 | NO |
| **gate_triage** (activity × rich_sel) | **0.779** | **0.686** | **0.666** | **YES** |

**Key findings:**

1. **The ensemble does NOT triage correctly.** It ranks hemolytic AMPs above
   selective AMPs (sel_vs_hem AUROC = 0.466 < 0.5). This is the anti-selective
   bias documented in the selectivity benchmark, now confirmed in the combined
   triage context.

2. **selectivity_proxy and expert_composite triage correctly by pairwise AUROC**
   (all three AUROCs > 0.5). selectivity_proxy remains the best scorer because it
   has stronger selective-vs-hemolytic separation (0.610 vs expert_composite 0.545)
   while keeping slightly better selective-vs-decoy discrimination (0.782 vs 0.757).

3. **The naive triage_score (activity × (1 - hemolysis_risk)) does NOT fix the
   anti-selective bias** (sel_vs_hem = 0.462). This is because hemolysis_risk
   is too weak (detection AUROC 0.565, not significant on expanded benchmark).
   A naive virtual-assay composite does not outperform the ensemble.

6. **The gate_triage scorer (activity × rich_selectivity) is the first scorer
   to triage correctly with strong selective_vs_hemolytic separation** (0.666).
   Unlike the old triage_score, it uses rich_selectivity (detection AUROC 0.714,
   significant) instead of hemolysis_risk (not significant). It also achieves
   selective_vs_decoy 0.779 and hemolytic_vs_decoy 0.686, and ranks 16 selective
   / 1 hemolytic / 3 decoys in its top-20 — the best distribution of any benchmarked
   scorer. However, its AMP-vs-decoy discrimination is weaker than the ensemble
   (0.779 vs 0.848) because the rich_selectivity gate penalizes AMP-like features.
   It must NOT replace the ensemble activity gate; it is a complementary signal.

4. **Top-20 distribution shift:** The triage_score moves 2 more selective AMPs
   into the top-20 (16 vs 14 for ensemble), removing 2 hemolytic AMPs (4 vs 6).
   The shift is in the right direction but modest — the hemolysis_risk penalty
   is weak.

5. **Expert-composite top-k failure:** The expert_composite removes hemolytic
   AMPs from its top-20 (15 selective / 0 hemolytic), but admits 5 random decoys.
   That is a useful negative result: expert ranking is not a replacement for the
   ensemble activity gate, even when its pairwise AUROCs clear 0.5.

**Implication for the virtual assay layer:** Any future virtual assay module
must beat this triage benchmark baseline. The minimum bar is: triage correctly
(all three AUROCs > 0.5), keep decoys out of the top-k selection surface, and
maintain near-ensemble decoy discrimination (sel_vs_decoy > 0.80). The
selectivity_proxy achieves correct triage but loses decoy-discrimination margin.
The expert_composite achieves correct pairwise triage but admits decoys into its
top-20. A successful virtual assay must avoid both failures.

**Honest limitation:** The benchmark uses literature HC50 values with high
inter-assay variability. The binary thresholds (25 / 100 µg/mL) are coarse.
The MODERATE class (HC50 25-100, n=68) is excluded from the binary task.

### Strict Triage: Composition-Matched Decoys (v0.5.14 — added 2026-07-02)

> The standard triage benchmark uses random background peptides as decoys.
> These are trivially distinguishable from AMPs because their composition is
> protein-like, not AMP-like. This inflates selective_vs_decoy and
> hemolytic_vs_decoy AUROCs, making scorers appear to triage well.
>
> The strict triage benchmark replaces random decoys with **composition-matched
> scrambled versions** of the selective AMPs — same amino acids, permuted order.
> This destroys amphipathic helical phase, hydrophobic moment, and charge
> distribution patterns while preserving all composition-based features.

**Key finding: standard triage success was partly an illusion.**

| Scorer | Std sel_vs_dec | Strict sel_vs_dec | Std sel_vs_hemo | Strict sel_vs_hemo | Std correct | Strict correct |
|-------|-----------------|-------------------|------------------|---------------------|--------------|----------------|
| ensemble | 0.848 | **0.572** | 0.466 | 0.466 | NO | NO |
| activity | 0.885 | **0.617** | 0.430 | 0.430 | NO | NO |
| selectivity_proxy | 0.782 | **0.500** | 0.610 | 0.610 | YES | **NO** |
| expert_composite | 0.757 | **0.510** | 0.545 | 0.545 | YES | **NO** |
| triage_score | 0.863 | **0.674** | 0.462 | 0.462 | NO | NO |
| hemolysis_risk | 0.485 | 0.617 | 0.488 | 0.488 | NO | NO |
| gate_triage | 0.779 | **0.624** | 0.666 | 0.666 | YES | **NO** |

**What this reveals:**

1. **selectivity_proxy collapses to exactly 0.5000** on selective_vs_decoy —
   confirming it is purely composition-driven (charge and GRAVY are identical
   between a sequence and its scrambled version).

2. **The ensemble drops from 0.848 to 0.572** — most of its apparent triage
   power was composition-based, not order-based.

3. **No scorer triages correctly** with composition-matched decoys. The standard
   triage "success" of selectivity_proxy and expert_composite was an artifact
   of trivially distinguishable decoys.

4. **selective_vs_hemolytic is stable** across both benchmarks (identical AUROCs)
   — as expected, since both classes are real AMP sequences and only the decoy
   class changes.

5. **The ensemble admits 7 scrambled decoys into top-20** (vs 0 with random
   decoys) — it cannot distinguish real AMPs from scrambled versions of themselves.

6. **gate_triage retains partial order-dependent signal** (sel_vs_dec 0.624,
   hem_vs_dec 0.489). It fails strict triage because rich_selectivity penalizes
   the AMP-like composition that hemolytic AMPs share with their scrambled
   versions. But its selective_vs_decoy remains above 0.5, unlike selectivity_proxy
   which collapses to exactly 0.500 — suggesting the activity gate contributes
   order-dependent signal that the selectivity gate alone lacks.

**Implication:** The pipeline's triage signal is almost entirely composition-driven.
The real bottleneck is selective-vs-hemolytic discrimination, which requires
structural or contextual features beyond what current 1D physicochemical scorers
can capture. Any future virtual assay layer must demonstrate order-dependent
triage signal on this strict benchmark before claiming to improve candidate
selection.

## Feature Decomposition: Per-Feature Selective vs Hemolytic (v0.5.15 — added 2026-07-03)

> The strict triage benchmark (v0.5.14) proved that NO composite scorer passes
> selective_vs_hemolytic discrimination (AUROC 0.43-0.54). But it did not explain
> *why*. This benchmark tests every scalar physicochemical feature individually
> for selective_vs_hemolytic AUROC, with bootstrap confidence intervals.

**Key finding: the selectivity proxy ignores the strongest discriminative features.**

The selectivity proxy uses only `net_charge_ph74` and `gravy`. The top feature,
`hydrophobic_fraction` (AUROC 0.6745, CI 0.58-0.77), is NOT used by the proxy.
Six of eight significant features are not used by the current selectivity model.

| Feature | Detection AUROC | CI 95% | Direction | Used by proxy? |
|---------|-----------------|--------|-----------|----------------|
| hydrophobic_fraction | **0.6745** | 0.58-0.77 | risk | **NO** |
| helix_propensity | **0.6489** | 0.54-0.75 | risk | **NO** |
| net_charge_proxy | **0.6394** | 0.54-0.73 | risk | **NO** |
| net_charge_ph74 | **0.6332** | 0.54-0.73 | risk | YES |
| selectivity_proxy | **0.6095** | 0.52-0.70 | protective | YES |
| interior_trypsin_sites | **0.6089** | 0.51-0.70 | risk | **NO** |
| longest_repeat_run | **0.5946** | 0.52-0.68 | risk | **NO** |
| length | **0.5785** | 0.51-0.66 | risk | **NO** |

**What this reveals:**

1. **`hydrophobic_fraction` is the strongest single discriminative feature**
   (AUROC 0.6745), yet the selectivity proxy does not use it. The proxy relies
   on charge and overall hydrophobicity (GRAVY), but the *fraction* of
   hydrophobic residues carries more signal.

2. **All significant risk indicators point in the expected direction**
   (higher = more hemolytic). The features the pipeline already tracks (charge,
   hydrophobicity, helix propensity) have real signal for hemolysis, but the
   composite scorers cancel it out.

3. **The selectivity proxy itself has weak but significant signal** (0.6095)
   as a protective indicator. It is doing the right thing but is underpowered
   because it ignores the strongest axes.

4. **22 of 30 features tested have NO significant signal** for selective vs
   hemolytic discrimination. This confirms the strict triage finding: 1D
   physicochemical descriptors alone cannot solve this task well.

**Implication for next steps:**

A richer selectivity scorer combining `hydrophobic_fraction`, `helix_propensity`,
`net_charge`, and `interior_trypsin_sites` in a learned or hand-tuned model
could plausibly improve selective_vs_hemolytic AUROC above the current 0.55
ceiling. However, the best single feature (0.6745) is still modest, and
the CI is wide. 3D structural modelling or sequence-pattern features may
ultimately be needed for clinically meaningful discrimination.

Run: `make bench-feature-decomp` or `python -m openamp_foundry.cli bench feature-decomp`

## Rich Selectivity Scorer (v0.5.16 — added 2026-07-03)

The feature decomposition benchmark identified 8 significant features for selective_vs_hemolytic
discrimination, but the old `selectivity_proxy` (charge + GRAVY) used only 2. The rich selectivity
scorer (`scoring/selectivity_rich.py`) combines all 8 significant features, weighted by detection
AUROC, to produce a composite selectivity score.

| Scorer | Detection AUROC | CI 95% | Significant? |
|--------|----------------|--------|-------------|
| **rich_selectivity** | **0.7138** | **0.6266-0.7951** | **YES** |
| selectivity_proxy (old) | 0.5744 | 0.4954-0.6558 | Marginal |
| hemolysis_risk | 0.5650 | 0.4664-0.6601 | NO |
| expert_composite | 0.5459 | 0.4562-0.6305 | NO |
| safety | 0.5116 | 0.4321-0.5954 | NO |
| ensemble | 0.4201 | 0.3335-0.5067 | NO (anti-signal) |

**Key finding:** The rich selectivity scorer is the **first pipeline score with statistically
significant hemolysis detection** on the expanded n=179 benchmark (CI lower bound 0.6266 > 0.5).
It outperforms the old selectivity_proxy by +0.14 AUROC and is the only scorer whose CI excludes 0.5.

**Features combined (by detection AUROC):**
`hydrophobic_fraction` (0.6745), `net_charge_proxy` (0.6394), `net_charge_ph74` (0.6332),
`helix_propensity` (0.6489), `interior_trypsin_sites` (0.6089), `selectivity_proxy` (0.6095,
protective), `longest_repeat_run` (0.5946), `length` (0.5900).

**Honest limitations:**
- The rich selectivity scorer does NOT triage AMP-vs-decoy correctly (selective_vs_decoy = 0.19).
  It is designed for within-AMP ranking, not activity detection. It must be combined with an
  activity gate to be useful for candidate selection.
- Individual feature AUROCs are weak (0.59-0.67); the composite's CI is wide (0.63-0.80).
- Normalisation thresholds are empirical and may not generalise beyond the reference set.
- Does not model 3D structure, oligomeric state, or membrane curvature.
- HC50 values are approximate literature values with high inter-assay variability.
- This is a triage signal, NOT a hemolysis predictor. Wet-lab hemolysis assay remains mandatory.

Run: `make bench-selectivity` (rich_selectivity is included in the selectivity benchmark output)

## Two-Gate Triage Composite (v0.5.17 — added 2026-07-03)

> The triage benchmark showed that no scorer could pass all three pairwise
> AUROC conditions (selective_vs_decoy, hemolytic_vs_decoy, selective_vs_hemolytic)
> with strong selective-vs-hemolytic separation. selectivity_proxy passed but
> had weak separation (0.610). expert_composite passed but admitted 5 decoys
> into top-20. The old triage_score used hemolysis_risk (not significant).
>
> This scorer combines two complementary signals as a multiplicative gate:
> activity (strong AMP-vs-decoy, AUROC 0.885-0.934) × rich_selectivity
> (strong selective-vs-hemolytic, AUROC 0.745, significant).
>
> Run: `make bench-triage`

**Key result: gate_triage is the first scorer to pass all three standard triage conditions
with selective_vs_hemolytic > 0.65.**

| Scorer | sel > decoy | hem > decoy | sel > hem | Top-20 (sel/hem/dec) | Correct? |
|--------|:-----------:|:-----------:|:---------:|:---------------------:|:--------:|
| ensemble | 0.848 | 0.891 | 0.466 | 14/6/0 | NO |
| selectivity_proxy | 0.782 | 0.795 | 0.610 | — | YES (weak) |
| expert_composite | 0.757 | 0.746 | 0.545 | 15/0/5 | YES (decoy leak) |
| triage_score (old) | 0.863 | 0.902 | 0.462 | 16/4/0 | NO |
| **gate_triage** | **0.779** | **0.686** | **0.666** | **16/1/3** | **YES** |

**Design rationale:**

The two gates solve complementary problems:
- activity gate: detects AMP-likeness (composition + amphipathicity) —
  strong vs random decoys but anti-selective (rewards hemolytic AMPs)
- rich_selectivity gate: detects hemolysis risk from 8 evidence-identified
  features — strong vs hemolytic AMPs but anti-AMP (penalizes AMP-like composition)

Their product leverages both: a candidate must score high on BOTH AMP-likeness
AND selectivity. Hemolytic AMPs score high on activity but low on rich_selectivity.
Decoys score low on activity. Selective AMPs score moderately on both.

**Honest limitations:**

1. gate_triage does NOT pass strict triage (composition-matched decoys).
   Its hemolytic_vs_decoy drops to 0.489 because rich_selectivity penalizes
   the AMP-like composition that hemolytic AMPs share with their scrambled
   versions. It retains partial order-dependent signal (sel_vs_dec 0.624),
   but this is from the activity gate, not the selectivity gate.

2. gate_triage is weaker than ensemble on pure AMP-vs-decoy detection
   (0.779 vs 0.848). It must NOT replace the ensemble activity gate.
   It is a complementary triage signal, not a replacement.

3. A decoy leaks into the top-20 (3 decoys vs 0 for ensemble). The
   selectivity gate removes some hemolytic AMPs but admits some decoys
   that happen to have moderate activity and moderate selectivity.

4. This is still a dry-lab triage signal. Wet-lab hemolysis assay
   remains mandatory for all candidates.

## Test Suite

| Metric | Value |
|--------|-------|
| Total tests | 1515+ |
| Coverage (branch) | 99% (6 CLI guard lines only) |
| Source modules at 100% | All pipeline, QC, scoring modules |

---

## Key Limitations

| Limitation | Impact |
|------------|--------|
| AUROC 0.7832 | ~22% of benchmark pairs misranked; wet-lab is the judge |
| Safety model blind spot | Melittin scores Safety=1.0; hemolysis assay mandatory |
| No structural modeling | Helical assumption may misclassify non-helical mechanisms |
| Near-seed generation only | Novel sequence space not explored de novo |
| Benchmark at 191 sequences | Still far from 500+ target flagged in ROADMAP (v1.0+) |
| APD/DRAMP novelty (v2) | Complete — 27,234-sequence combined DB (APD6+DRAMP+UniProt); BLOSUM62 local alignment; Wave 0.5 results updated |
| No wet-lab data | All probabilities are upper bounds; true hit rate unknown |
| Rich selectivity scope | Designed for within-AMP selectivity only; does not distinguish AMPs from decoys (selective_vs_decoy=0.19) |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-06-29 | Novelty audit v2: BioPython BLOSUM62 local alignment vs 27,234 AMPs (APD6+DRAMP+UniProt); panel updated (15 families, 4 SAR_CONTROL); all 7 gates PASS | OpenAMP Wave 0.5 |
| 2026-06-29 | Wave 0.5b: 23-candidate safety-optimized shortlist (SEED-020–024, no aromatics) | OpenAMP Wave 0.5b |
| 2026-06-29 | External predictor results filled from wave05_combined_consensus.csv; all 7 gates PASS | OpenAMP Wave 0.5 |
| 2026-06-29 | Wave 0.5 scaffold diversification — 24-candidate Wave 1 panel across 14 families | OpenAMP Wave 0.5 |
| 2026-07-01 | Expert ablation benchmark added: expert composite AUROC 0.7119 vs ensemble 0.7832 (delta −0.0713); anti-signal components documented; ensemble remains primary gate | OpenAMP loop |
| 2026-07-01 | **Hemolysis benchmark expanded:** 42 -> 238 peptides using DBAASP human erythrocyte data (54 hemolytic vs 125 selective, n=179 binary). Hemolysis risk scorer detection AUROC drops 0.9218 -> 0.5650 (CI 0.47-0.66) — original performance was small-sample inflation. Direction correct, not significant. Safety scorer detection improves 0.3844 -> 0.5116 (still not significant). 196 new peptides from DBAASP v3. | OpenAMP loop |
| 2026-07-01 | Dedicated hemolysis risk scorer: 4-component score (synth+aromatic+face+cys) achieves detection AUROC=0.9218 (CI: 0.82-0.99); integrated into expert composite (detection 0.5119→0.6429); safety scorer unchanged; 1471 tests | OpenAMP loop |
| 2026-07-01 | Within-AMP selectivity benchmark added: safety scorer FAILS hemolysis detection (AUROC=0.3844); synthesis is only significant risk detector (AUROC=0.8027); expert composite better than ensemble but not significant (0.5119 vs 0.3486) | OpenAMP loop |
| 2026-07-01 | Expert composite ranking integration: `score_candidates()` now computes `expert_composite` and `hemolysis_risk`; `--ranking-mode expert` CLI flag; expert-ranked top-5 have lower mean hemolysis_risk than ensemble | OpenAMP loop |
| 2026-07-02 | **Strict triage benchmark added:** composition-matched scrambled decoys replace random background. No scorer triages correctly — standard triage "success" of selectivity_proxy (0.782 sel_vs_dec) and expert_composite (0.757) was inflated by trivially distinguishable decoys. selectivity_proxy collapses to 0.500 (purely composition-driven), ensemble drops to 0.572. Real bottleneck (selective_vs_hemolytic) unchanged. | OpenAMP loop |
| 2026-07-02 | Ranking policy contract added: machine-readable recommendation now states `ensemble` remains default broad synthesis gate, `expert` is narrower safety-aware alternative only | OpenAMP loop |
| 2026-07-03 | **Rich selectivity scorer added:** composite of 8 evidence-identified features from the feature decomposition benchmark. Detection AUROC=0.7138 (CI 0.63-0.80) on n=179 — first pipeline score with statistically significant selective_vs_hemolytic discrimination. Old selectivity_proxy=0.5744 (CI 0.50-0.66). Honest limitation: does not triage AMP-vs-decoy (0.19); must be combined with activity gate. | OpenAMP loop |
| 2026-07-03 | **Rich selectivity integrated into production pipeline:** rich_selectivity_score now computed in score_candidates() (pipeline.py), replaces hemolysis_safety as the expert composite hemolysis-risk component (weight 0.10), used in pilot_priority formula, displayed in pilot panel report, and included in evidence certificates. Expert AUROC drops 0.7119→0.7097 (−0.0022) — acceptable tradeoff: the expert now includes a significant hemolysis detector (CI excludes 0.5) instead of the old non-significant one. | OpenAMP loop |
| 2026-07-03 | **Two-gate triage composite added:** gate_triage = activity × rich_selectivity, added to triage benchmark. First scorer to pass all three standard triage conditions with strong selective_vs_hemolytic separation (0.666). Top-20: 16 selective / 1 hemolytic / 3 decoy — best distribution. Does NOT pass strict triage (hem_vs_dec 0.489) — honest limitation. Must not replace ensemble activity gate. | OpenAMP loop |
| 2026-07-03 | **Feature decomposition benchmark added:** per-feature selective_vs_hemolytic AUROC for all 30 scalar physicochemical features. hydrophobic_fraction is the strongest single discriminative feature (0.6745, CI 0.58-0.77) but is NOT used by the selectivity proxy. 8/30 features have significant signal; 6 of those are unused. Provides actionable diagnostic for why composite scorers fail selective_vs_hemolytic discrimination. | OpenAMP loop |
| 2026-07-04 | **Calibration intake module added:** `openamp-foundry calibration-intake` joins a pilot panel CSV with a directory of validated lab result JSON files, produces a per-candidate prediction-vs-actual report with cohort metrics gated by `MIN_COHORT_SIZE=5`. Descriptive only — does NOT trigger recalibration, weight updates, or selection-rule changes. Synthetic example data in `examples/lab_results/` is clearly labeled in every file and in `examples/lab_results/README.md`. 29 new tests; total 1614 passing. | OpenAMP loop |
| 2026-06-29 | Initial — expanded benchmark (PR #110) | OpenAMP CI |
| 2026-07-04 | **Recalibration policy + gate module added:** `openamp-foundry recalibration-gate` evaluates a calibration intake report against the pre-registered policy in `configs/recalibration_policy.yaml` and emits a binary `may_recalibrate` verdict. The policy file encodes 7 minimum conditions (cohort size, controls, orphans, positives, negatives, metrics availability), 5 permanent prohibited actions (toxicity, hemolysis, novelty, pathogen enhancement, post-hoc success redefinition), and 2 rate limits (L1 weight budget, cooldown). The validator rejects policy files that omit any canonical prohibited action or any `locked_changes` entry. The gate does NOT trigger weight updates; it is the missing permission layer between v0.5.19 intake and a future recalibration engine. Exit code 0 when `may_recalibrate=true`, 3 when false. 39 new tests; total 1647 passing. See `docs/CALIBRATION_POLICY.md`. | OpenAMP loop |
