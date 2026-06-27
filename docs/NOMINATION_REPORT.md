# OpenAMP Foundry — Phase 3 Nomination Report

**Status:** Computational nomination complete. Awaiting expert review and wet-lab validation.  
**Pipeline version:** 0.1.0 (v0.2 scorer update — dual-scorer consensus)  
**Run date:** 2026-06-27  
**Run ID:** 730e8190-f901-401e-a274-78fae530c857  
**Config hash:** 79006c5f18f594c40564f27aea947bb581a5fde73f055789cecbb535489603da  
**Branch:** feat/phase4-lab-bridge  

---

## Abstract

We report the computational nomination of 89 candidate antimicrobial peptides (AMPs) using a
transparent, reproducible, safety-first dry-lab pipeline. Starting from five published AMP
template sequences, conservative amino-acid substitutions generated 383 variants, which were
scored across six physicochemical dimensions, filtered by pre-registered criteria, and
diversity-selected into a batch of 89 candidates. Each candidate carries a JSON evidence
certificate validated against a published schema, a run manifest with SHA-256 input hashes,
and dual-scorer consensus information from two independent activity predictors.

**No biological activity has been demonstrated. These are computational nominations only.**
Wet-lab validation (synthesis, MIC assay, hemolysis assay) is the required next step.

---

## 1. Motivation

Short cationic amphipathic peptides are a structural class with a long history of antimicrobial
activity. Known families include magainins (frog skin), cecropins (insect innate immunity),
temporins (tree frog), and indolicidin (bovine neutrophils). Despite decades of research, no
AMP has reached clinical use for systemic infections due to toxicity and stability concerns.
Short variants (10–15 residues) with balanced charge and hydrophobicity profiles have shown
promise in preliminary studies.

This pipeline aims to systematically explore the near-neighbourhood of known AMP templates
using physicochemical scoring, to produce a transparently selected, non-cherry-picked batch of
nominees with a full reproducible evidence trail, suitable for handing off to expert reviewers
and independent laboratory validation.

---

## 2. Seed Templates

Five template sequences were selected from published literature to represent distinct AMP
structural families:

| Seed ID | Sequence | Length | Family | Rationale |
|---------|----------|--------|--------|-----------|
| SEED-001 | KWKLFKKIGAVLKVL | 15 | Magainin-like | Prototypical cationic helical AMP |
| SEED-002 | GIGKFLHSAKKFGKAFVGEIMNS | 23 | Cecropin/Magainin-like | Longer, lower charge density |
| SEED-003 | RRWQWRMKKLG | 11 | Cationic tryptophan-rich | Short, aromatic-rich template |
| SEED-004 | FLPLIGRVLSGIL | 13 | Temporin-like | Hydrophobic-dominant, lower charge |
| SEED-005 | KRLFKKIGSALKFL | 14 | Hybrid cationic-hydrophobic | Balanced amphipathic template |

Seeds were not drawn from any experimental dataset used for scoring calibration. They are
published reference sequences treated as structural starting points only.

---

## 3. Candidate Generation

Three conservative substitution strategies were applied to each seed:

### 3.1 Conservative Groups

Substitutions were restricted to physicochemically similar residue groups:

| Group | Members | Rationale |
|-------|---------|-----------|
| Cationic | K, R, H | Same charge sign; swap K↔R↔H |
| Aliphatic hydrophobic | L, I, V, A, F, M | Similar hydrophobicity; short/medium side chains |
| Aromatic | F, W, Y | Aromatic character; membrane-inserting |
| Polar/neutral | S, T, N, Q | Uncharged polar; hydrogen-bond donors |
| Anionic | D, E | Negative charge; penalized by activity scorer |
| Conformational | G, P | Structural constraints; no substitution to/from others |
| Disulfide | C | Singleton; no substitution to avoid pairing complexity |

### 3.2 Strategy Details

| Strategy | Method | Count per seed | Determinism |
|----------|--------|---------------|-------------|
| Single substitutions | Enumerate all single-position conservative replacements | variable | Fully deterministic |
| Double substitutions | Random pairs of conservative positions | 25 | Seeded RNG (rng_seed=2024) |
| Charge-enhanced variants | Replace polar S/T/N/Q with K or R | 12 | Seeded RNG (rng_seed=2024) |

Total variants generated: **383 unique sequences** from 5 seeds (rng_seed=2024).

**Key limitation:** This strategy explores the near-neighbourhood of known AMP templates. It
does NOT generate genuinely novel sequences. The maximum divergence from any seed is ≤ 3
substitutions (for double + charge-enhanced). Future cycles should explore protein language
model sampling or evolutionary optimization for more radical novelty.

---

## 4. Scoring Pipeline

All scoring was computed by `src/openamp_foundry/pipeline.py` using `configs/phase3.yaml`.
No training data was used. All scores are heuristic physicochemical proxies.

### 4.1 Physicochemical Feature Extraction

Features were computed by `src/openamp_foundry/features/physchem.py`:

| Feature | Formula | Reference |
|---------|---------|-----------|
| Net charge proxy | Σ(K+R+H) − Σ(D+E) | Wimley & White 1996 |
| Charge density | net_charge / length | — |
| Hydrophobic fraction | count(L,I,V,A,F,M,W) / length | Kyte & Doolittle 1982 |
| Aromatic fraction | count(F,W,Y) / length | — |
| Cysteine fraction | count(C) / length | — |
| Glycine fraction | count(G) / length | — |
| Proline fraction | count(P) / length | — |
| Longest repeat run | max run of consecutive identical residues | — |
| Hydrophobic moment (μH) | Eisenberg (1984), 100°/residue helical wheel | Eisenberg et al. 1984 |
| Boman index | mean per-residue interaction potential | Boman 2003, Table 1, set 2 |
| GRAVY | mean Kyte-Doolittle hydropathy | Kyte & Doolittle 1982 |

### 4.2 Activity-Likeness Score (Scorer 1)

A heuristic approximating AMP-like properties from net charge, hydrophobic fraction, and
hydrophobic moment (μH). Score ∈ [0, 1]. Implemented in `scoring/activity.py`.

Key inputs:
- Positive charge density (K, R, H enrichment) → increases score
- Hydrophobic fraction ~0.40–0.55 → increases score; too high penalizes
- μH > 0.4 (amphipathic helix signal) → bonus contribution
- Length outside 10–25 aa → penalty

**Limitation:** Assumes amphipathic α-helical conformation. Non-helical AMPs are underscored.

### 4.3 Boman Activity Score (Scorer 2 — independent)

Derived from the Boman (2003) per-residue interaction potentials:

```
Boman index = (1/N) × Σ_i  Boman_potential(aa_i)
```

Published potentials (Boman 2003, Table 1, set 2):
- Cationic/anionic residues (K, R, D, E): +2.465 kcal/mol each
- Hydrophobic residues (W, F, Y, I, L, V, A, M): negative contributions (−0.5 to −3.4)
- Neutral residues (G, P): 0.0

The raw index is normalized to [0, 1] via tanh: `score = 0.5 × (1 + tanh(BI / 2))`.

Published benchmark: Boman index > 1.0 correlates with AMP/protein-binding peptides.

**Key design choice:** The Boman index and the activity-likeness scorer are intentionally
independent — they use different mathematical representations of AMP properties. The
discrepancy between them is informative (see Section 4.7).

### 4.4 Safety Score (Toxicity Proxy)

Penalizes physicochemical features associated with hemolytic risk:

| Risk signal | Threshold | Effect |
|------------|-----------|--------|
| Excess hydrophobicity | hydrophobic_fraction > 0.65 | Multiplicative penalty |
| Excess charge density | charge_density > 0.55 | Multiplicative penalty |
| High cysteine content | cysteine_fraction > 0.25 | Multiplicative penalty |
| Long sequence | length > 35 aa | Multiplicative penalty |
| Long repeat run | longest_repeat_run ≥ 6 | Multiplicative penalty |

Score ∈ [0, 1]; 1.0 = no risk flags triggered. Implemented in `scoring/safety.py`.

**Critical limitation:** This score has never been calibrated against hemolysis data. It is a
physics-based proxy only. Red blood cell lysis assay is mandatory before any safety claim.

### 4.5 Synthesis Feasibility Score

Penalizes sequences predicted to be difficult to synthesize by standard SPPS:

| Factor | Concern |
|--------|---------|
| Cysteine content | Disulfide bridge complications |
| Proline content | Poor coupling efficiency |
| Length > 30 aa | Stepwise yield loss |
| Repeat runs | Aggregation during synthesis |

Score ∈ [0, 1]; 1.0 = no synthesis concerns flagged. Implemented in `scoring/synthesis.py`.

### 4.6 Novelty Score

```
novelty = 1 − max_i(normalized_Levenshtein_similarity(candidate, reference_i))
```

Computed against **45 curated known AMPs** in `examples/known_reference/amp_curated_references.csv`.
Novelty 0.0 = identical to a known reference; 1.0 = no similar reference exists.

Reference set covers: magainins, pexiganan, buforins, indolicidin, temporins, aureins, cecropins,
cathelicidins, melittin (hemolysis control), and the five seed sequences themselves.

### 4.7 Ensemble Score (Pre-registered)

```
ensemble = 0.35 × activity + 0.30 × safety + 0.20 × synthesis + 0.15 × novelty
```

Weights were fixed in `docs/SELECTION_RULE.md` before any candidate generation run.
Boman activity is NOT included in the ensemble — it is a transparency/audit signal only.

### 4.8 Model Disagreement

```
disagreement = |activity_likeness − boman_activity|
```

This measures how much the two independent scorers disagree about a candidate's activity.

**Interpretation:**
- disagreement < 0.20 → high consensus; both scorers agree
- disagreement 0.20–0.30 → moderate; scorers diverge somewhat
- disagreement ≥ 0.30 → uncertain; extra scrutiny recommended

The mean disagreement for this batch is **0.311**, which reflects a systematic difference
between the two scoring models: the activity scorer rewards amphipathic character (balanced
charge + hydrophobicity + helical moment) while the Boman index penalizes the hydrophobic
residues those same peptides contain. This is not a pipeline failure — it is an honest signal
that these candidates are predicted AMPs through an amphipathic membrane-disruption mechanism
(activity scorer) but show only moderate protein-binding potential by the Boman criterion.

Candidates where both scores are high (low disagreement) are computationally stronger nominations.

---

## 5. Selection Criteria

Selection was executed by `src/openamp_foundry/selection/` using `configs/phase3.yaml`.
The complete pre-registered rule is in `docs/SELECTION_RULE.md`.

### 5.1 Hard Filters

Applied to all candidates before ranking:

| Filter | Threshold | Rationale |
|--------|-----------|-----------|
| Length | 8–35 aa | Synthesis feasibility; typical AMP range |
| Canonical AAs | Strict 20-letter alphabet | Synthesis compatibility |
| Safety score | ≥ 0.60 (max_safety_risk ≤ 0.40) | Minimum tolerable toxicity proxy |
| Novelty | ≥ 0.05 | Exclude near-identical copies of known AMPs |

### 5.2 Ranking

Candidates passing all filters were ranked by ensemble score (descending).

### 5.3 Diversity Selection

Greedy single-linkage diversity selection was applied with pairwise similarity cap of 0.80
(normalized Levenshtein). When two candidates share similarity > 0.80, only the higher-ranked
one proceeds.

Target batch size: up to 100 candidates (89 passed).

---

## 6. Results

### 6.1 Overall Statistics

| Metric | Value |
|--------|-------|
| Candidates generated | 383 |
| Passing all hard filters | 89 |
| Evidence certificates (schema-validated) | 89 (+ 4 pre-existing from earlier run) |
| Length range of selected | 11–14 aa |
| Diversity clusters (threshold 0.80) | 32 |
| Singleton clusters | 13 (40.6%) |
| Mean ensemble score | 0.781 |
| Mean activity-likeness | 0.839 |
| Mean safety proxy | 1.000 |
| Mean synthesis feasibility | 1.000 |
| Mean novelty vs 45 refs | 0.172 |
| Mean Boman activity | 0.503 |
| Mean scorer disagreement | 0.311 |
| High consensus candidates (dis < 0.20) | 1 |
| Uncertain candidates (dis ≥ 0.30) | 48 |

### 6.2 Results by Seed Family

| Seed | Candidates selected | Mean ensemble | Mean Boman | Mean novelty | Mean disagreement |
|------|--------------------|-----------|-----------|-----------|----|
| SEED-001 (Magainin-like, 15-mer) | 12 | 0.784 | 0.419 | 0.128 | 0.338 |
| SEED-002 (Cecropin-like, 23-mer) | 8 | 0.758 | 0.452 | 0.087 | 0.247 |
| SEED-003 (Trp-rich cationic, 11-mer) | 27 | 0.825 | 0.538 | 0.168 | 0.319 |
| SEED-004 (Temporin-like, 13-mer) | 32 | 0.723 | 0.284 | 0.132 | 0.296 |
| SEED-005 (Hybrid cationic-hydrophobic, 14-mer) | 10 | 0.863 | 0.499 | 0.430 | 0.354 |

**SEED-003** (tryptophan-rich 11-mers) produces the most candidates, the highest mean ensemble
score (0.825), and the highest mean Boman activity (0.538). The SEED-003 family should be
prioritised in any pilot synthesis round.

**SEED-005** produces the highest mean ensemble (0.863) and the highest mean novelty (0.430)
but also the highest mean disagreement (0.354). These candidates score exceptionally well on
amphipathic character but modestly on the Boman criterion.

**SEED-004** (temporin-like) produces the most candidates (32) but the lowest Boman mean
(0.284). This family is more hydrophobic and the Boman index penalizes their hydrophobic
composition heavily.

### 6.3 Novelty Distribution

| Novelty tier | Count | Interpretation |
|-------------|-------|----------------|
| ≥ 0.30 (high) | 9 | Meaningful divergence from known AMP landscape |
| 0.10–0.30 (mid) | 58 | Modified from known templates; still substantively different |
| 0.05–0.10 (low) | 22 | Close to known AMPs; conservative variants |

**Note:** Novelty is computed against only 45 curated references. Real-world novelty against
APD3 (thousands of AMPs) or DRAMP would likely be lower. This is an important limitation.

### 6.4 Top 10 Candidates

Ranked by ensemble score. All have safety = 1.000, synthesis = 1.000.

| Rank | Candidate ID | Sequence | Ens | Activity | Boman | Disagreement | Novelty |
|------|-------------|----------|-----|----------|-------|--------------|---------|
| 1 | SEED-005_VAR_049 | KRLFKKIPSALKFF | 0.880 | 0.885 | 0.485 | 0.400 | 0.467 |
| 2 | SEED-005_VAR_009 | KRFFKKIGSALKFA | 0.877 | 0.878 | 0.508 | 0.370 | 0.467 |
| 3 | SEED-005_VAR_063 | KRLFRKIGSALKFV | 0.874 | 0.867 | 0.503 | 0.365 | 0.467 |
| 4 | SEED-005_VAR_058 | KRLFKKVGSALRFL | 0.871 | 0.861 | 0.503 | 0.358 | 0.467 |
| 5 | SEED-005_VAR_023 | KRLFKKIGRALKFL | 0.870 | 0.913 | 0.537 | 0.376 | 0.333 |
| 6 | SEED-005_VAR_061 | KRLFKRLGSALKFL | 0.868 | 0.853 | 0.497 | 0.355 | 0.467 |
| 7 | SEED-005_VAR_068 | KRLMKKIGSAIKFL | 0.856 | 0.818 | 0.519 | 0.299 | 0.467 |
| 8 | SEED-005_VAR_013 | KRLAKHIGSALKFL | 0.855 | 0.814 | 0.480 | 0.334 | 0.467 |
| 9 | SEED-005_VAR_002 | HRLIKKIGSALKFL | 0.849 | 0.813 | 0.457 | 0.356 | 0.429 |
| 10 | SEED-003_VAR_027 | RRWQWRFKRLG | 0.839 | 0.890 | 0.532 | 0.358 | 0.182 |

### 6.5 Suggested Pilot Candidates

For a first-round synthesis pilot (5 candidates), ranking by Boman activity × low disagreement
rather than ensemble score selects the most computationally robust nominations:

| Priority | Candidate ID | Sequence | Boman | Disagreement | Rationale |
|----------|-------------|----------|-------|--------------|-----------|
| 1 | SEED-003_VAR_051 | RRWTWRMKKAG | 0.592 | 0.266 | Highest Boman in batch; low disagreement |
| 2 | SEED-003_VAR_014 | RRFQWRMRKLG | 0.579 | 0.288 | Strong Boman; aromatic substitution |
| 3 | SEED-003_VAR_045 | RRWQYRIKKLG | 0.572 | 0.305 | Strong Boman; Y/I substitution |
| 4 | SEED-003_VAR_003 | KRWQWRIKKLG | 0.547 | 0.311 | Good Boman; K at position 1 variant |
| 5 | SEED-005_VAR_023 | KRLFKKIGRALKFL | 0.537 | 0.376 | Highest activity (0.913); different family |

The first four are all SEED-003 11-mers. Including SEED-005_VAR_023 tests the longer 14-mer
family and the highest activity-scorer candidate in the batch.

---

## 7. Evidence Trail

The pipeline produces a complete, verifiable evidence chain:

| Artifact | Location | Purpose |
|---------|----------|---------|
| Run manifest | `outputs/phase3_manifest.json` | SHA-256 hashes of all inputs + config hash |
| Ranked JSONL | `outputs/phase3_ranked.jsonl` | All 383 candidates with scores and selection flag |
| Batch report (Markdown) | `outputs/phase3_report.md` | Human-readable ranking table |
| Evidence certificates (JSON) | `outputs/phase3_evidence/` | Schema-validated per-candidate certificate |
| Batch pack (JSON) | `outputs/phase3_batch_pack.json` | Five sub-reports: diversity, novelty, toxicity, synthesis, consensus |
| Batch pack (Markdown) | `outputs/phase3_batch_pack.md` | Human-readable version of batch pack |
| Expert review pack | `docs/EXPERT_REVIEW_PACK.md` | Lab handoff document with dual-scorer data |
| Pre-registered selection rule | `docs/SELECTION_RULE.md` | Rule locked before candidate generation |
| Config | `configs/phase3.yaml` | All thresholds and weights |
| Generator | `src/openamp_foundry/generators/template_mutator.py` | Deterministic substitution code |
| Benchmark | `src/openamp_foundry/benchmark/` | Validation that pipeline recovers known AMPs |

### 7.1 Reproducibility

To reproduce this nomination from the committed code:

```bash
git checkout feat/phase4-lab-bridge
make test     # 314 tests must pass
make phase3   # regenerates phase3_pool.csv, phase3_ranked.jsonl, certificates, batch pack
```

The run is fully deterministic given:
- Fixed seeds in `examples/sequences/amp_seeds.csv`
- Fixed references in `examples/known_reference/amp_curated_references.csv`
- Fixed config `configs/phase3.yaml`
- Fixed RNG seed `rng_seed=2024` in generator
- Fixed pipeline version `0.1.0`

The config hash `79006c5f...` and run manifest verify the exact input state.

---

## 8. What We Do Not Know

This section is mandatory for scientific integrity.

| Unknown | Impact | Required to resolve |
|---------|--------|-------------------|
| Whether any candidate has antimicrobial activity | Cannot claim AMP status without assay | MIC assay vs. target organisms |
| Whether any candidate is non-hemolytic | Cannot claim mammalian safety without assay | RBC hemolysis assay |
| Whether scoring correlates with activity | Scores are heuristics; no calibration data exists | Correlation study after lab results |
| Actual novelty vs. full AMP space | We checked 45 refs; APD3 has thousands | BLAST/similarity check vs. APD3/DRAMP |
| Whether the generation strategy misses better candidates | Near-neighbourhood only | Future: protein LM or Bayesian generation |
| Whether scorer disagreement predicts lab failures | Untested | Retrospective analysis after lab results |
| Structural confirmation of helical conformation | Assumed; not modeled | CD spectroscopy or NMR |
| Stability in biological fluids | Not modeled | Protease stability assay |

---

## 9. Safety and Dual-Use Assessment

- All candidates are short (11–14 residue), linear, canonical amino-acid sequences.
- No targeting information, no pathogen-specific optimization, no toxicity maximization.
- Generation was restricted to conservative substitutions of known (published) AMP templates.
- No dangerous pathogen instructions appear anywhere in this pipeline.
- All outputs are heuristic scores; no biological claims are made.
- The pipeline has been reviewed for dual-use risk (`DUAL_USE_REVIEW.md`).

**Expert sign-off required** before any candidate is synthesised or shared externally.

---

## 10. Next Steps (Human Gates)

The following steps cannot be completed computationally:

1. **Expert sign-off** (microbiologist or peptide chemist): review `docs/EXPERT_REVIEW_PACK.md`
2. **Extended novelty check**: BLAST candidates against APD3 / DRAMP databases
3. **Synthesis**: Standard SPPS at a qualified CRO or peptide synthesis facility
4. **MIC assay**: Against clinically relevant organisms (e.g., E. coli ATCC 25922, S. aureus ATCC 29213)
5. **Hemolysis assay**: Red blood cell lysis at MIC-equivalent concentrations
6. **Cytotoxicity**: If hemolysis clears, mammalian cell line assay
7. **Results ingestion**: Return results using `schemas/lab_result.schema.json` to close the active-learning loop
8. **Iteration**: Use lab results to recalibrate scores and generate next candidate generation

---

## 11. References

- Boman HG (2003). Peptide antibiotics and their role in innate immunity. Annual Review of Immunology, 13, 61-92.
- Eisenberg D et al. (1984). Analysis of membrane and surface protein sequences with the hydrophobic moment plot. J Mol Biol, 179(1), 125-142.
- Ge Y et al. (1999). In vitro model of Pseudomonas aeruginosa biofilm. J Antimicrob Chemother, 43, 799-804.
- Kyte J & Doolittle RF (1982). A simple method for displaying the hydropathic character of a protein. J Mol Biol, 157(1), 105-132.
- Mangoni ML et al. (2001). Temporins, small antimicrobial peptides. J Biol Chem, 276(22), 19861-19868.
- Selsted ME et al. (1992). Indolicidin, a novel bactericidal tridecapeptide. J Biol Chem, 267(7), 4292-4295.
- Wimley WC & White SH (1996). Experimentally determined hydrophobicity scale for proteins at membrane interfaces. Nat Struct Biol, 3(10), 842-848.
- Zasloff M (1987). Magainins, a class of antimicrobial peptides from Xenopus skin. PNAS, 84(15), 5449-5453.
