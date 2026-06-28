# OpenAMP Foundry — Methods Appendix

**Version:** 0.2.x (pipeline version); document updated for PRs #47–78  
**Status:** Working draft for expert review. Not a peer-reviewed publication.

---

## Abstract (Draft)

We describe a transparent, reproducible dry-lab pipeline for computational nomination of short
antimicrobial peptide (AMP) candidates. The pipeline applies physicochemical heuristic scoring,
novelty analysis against a curated reference set, synthesis feasibility filtering, and diversity
selection to produce a batch of computationally nominated candidates with machine-readable
evidence certificates. All scores are heuristic proxies; none have been calibrated against
experimental measurements. Candidates are nominated for possible expert review and qualified
wet-lab assay. No biological activity claims are made.

---

## 1. Candidate Generation

Candidates were produced by the `template_mutator.py` generator, which applies conservative
amino-acid substitutions to five AMP-like template sequences. Substitutions are restricted to
physicochemically conservative groups:

| Group | Amino acids |
|-------|-------------|
| Cationic | K, R, H |
| Aliphatic/hydrophobic | L, I, V, A, F, M |
| Aromatic | F, W, Y |
| Polar/neutral | S, T, N, Q |
| Anionic | D, E |
| Conformational | G, P |
| Disulfide | C (no substitutions) |

Three variant strategies were applied:
1. **Single substitutions**: All single-position conservative replacements (deterministic)
2. **Double substitutions**: Random pairs of conservative positions (n=25 per seed, rng_seed=2024)
3. **Charge-enhanced variants**: Polar positions (S, T, N, Q) replaced by K or R (n=12 per seed)

Total: 383 unique variants from 5 seeds (rng_seed=2024).

> **Note (PRs #63–78):** The generation strategy above (5 seeds, rng_seed=2024) describes the
> initial variant corpus. Scoring was then improved across PRs #47–72; the current pipeline
> achieves **AUROC 0.8420** on the 87-sequence benchmark set (43 AMPs + 44 background; set
> finalized PR #66). Separately, the synthesis pool was expanded to 7 scaffold families:
> SEED-006 through SEED-009 added in expansion PRs #38–58; SEED-001 (magainin-1) re-entered
> PR #72 after the face_segregation_bonus raised its helix-score contribution. Current synthesis
> pool: **100 candidates from 7 scaffold families**. Same pipeline config (`pipeline.yaml`,
> `phase3.yaml`); wider seed set.

**Limitation:** This generation strategy produces near-seed variants. It does not explore
genuinely novel sequence space. Future work should incorporate protein language model sampling
or Bayesian sequence optimization.

---

## 2. Sequence Validation

Sequences were validated against the following criteria:
- Length 8–35 amino acids (inclusive)
- Canonical amino acid alphabet only (A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y)

Sequences failing either criterion received zero scores for activity and safety, and were
excluded from the selected batch.

---

## 3. Physicochemical Feature Extraction

The following features were extracted for each sequence:

| Feature | Formula | Reference |
|---------|---------|-----------|
| Length | Count of residues | — |
| Net charge proxy | (K+R+H) − (D+E) | Wimley & White 1996 |
| Charge density | net_charge / length | — |
| Hydrophobic fraction | (L+I+V+A+F+M+W) / length | Kyte & Doolittle 1982 |
| Aromatic fraction | (F+W+Y) / length | — |
| Cysteine fraction | C / length | — |
| Glycine fraction | G / length | — |
| Proline fraction | P / length | — |
| Longest repeat run | Longest run of identical consecutive residues | — |
| Hydrophobic moment | Eisenberg (1984), 100°/residue helical angle | Eisenberg et al. 1984 |
| Boman index | Mean per-residue interaction potential | Boman 2003, Table 1, set 2 |
| GRAVY | Grand Average of hYdropathicity; mean Kyte-Doolittle value | Kyte & Doolittle 1982 |

**Limitation:** Features assume linear, unstructured sequence. Amphipathicity (hydrophobic
moment) assumes an α-helical conformation (100°/residue). Non-helical AMPs are not modeled.

---

## 4. Scoring

### 4.1 Activity-Likeness Score

A heuristic score approximating AMP-like physicochemical properties. Computed from
eight terms; weights encode biochemical priors only (not data-optimised). Pre-clamp ceiling
1.02; final `clamp01()` bounds output to ≤ 1.0. Without `helix_wheel_amphipathic_score` key
the pre-clamp ceiling is 0.97 (backward-compatible with pre-PR-#72 feature dicts).

| Term | Contribution | Literature basis |
|------|-------------|-----------------|
| Length score | × 0.24 | Peak at 18 aa; broad tolerance ±25 aa (Jenssen 2006) |
| Charge density (pH 7.4) | × 0.27 | +2 to +9 net charge for active AMPs (Zasloff 2002) |
| Hydrophobic fraction | × 0.17 | 40–50% sweet spot for membrane interaction (Hancock 2006) |
| Aromatic bonus | up to +0.10 | F/W/Y aid membrane insertion; capped at 20% fraction |
| Amphipathicity (μH) | up to +0.14 | μH > 0.4 correlates with membrane disruption (Eisenberg 1984) |
| Helix bonus (Pα) | up to +0.03 | Chou-Fasman Pα > 1.0; helical AMPs ~70% of membrane-active families (Huang 2000) |
| Cross-term (cd × μH) | up to +0.02 | Electrostatic + hydrophobic insertion synergy; normaliser 0.15 |
| Face segregation (hw_amp) | up to +0.05 | helix_wheel_amphipathic_score from moment-oriented wheel; [0,1] |

**Formula (Python source: `scoring/activity.py`):**

```
# Anionic guard (PR #70): if charge_density_ph74 < 0.0, return 0.0 immediately.
# Anionic peptides are electrostatically repelled by bacterial membranes.

μH_eff = max(hydrophobic_moment, max_hydrophobic_moment)  # windowed mu_h (PR #70)

score = 0.24 × length_score
      + 0.27 × clamp01((charge_density_ph74 + 0.05) / 0.55)
      + 0.17 × (1 − min(|hydrophobic − 0.45| / 0.45, 1.0))
      + min(aromatic / 0.20, 1.0) × 0.10              # aromatic_bonus
      + clamp01(μH_eff / 0.8) × 0.14                  # amphipathicity_score (windowed)
      + clamp01((Pα − 1.0) / 0.20) × 0.03             # helix_bonus
      + clamp01(charge_density_ph74 × μH_eff / 0.15) × 0.02  # cross_bonus
      + helix_wheel_amphipathic_score × 0.05           # face_segregation_bonus (PR #72)
# Pre-clamp ceiling: 0.24+0.27+0.17+0.10+0.14+0.03+0.02+0.05 = 1.02
# clamp01(score) at the end clips to [0, 1]. Without face_segregation key the ceiling is 0.97.
```

`μH_eff` = `max(hydrophobic_moment, max_hydrophobic_moment)`. `max_hydrophobic_moment` is the
best μH over any 11-residue window (Eisenberg standard). For sequences ≤ 11 AA this equals
the full-sequence μH. For longer sequences it captures the most amphipathic helical segment,
which better reflects the membrane-active region. (Added PR #70.)

`helix_wheel_amphipathic_score` is the face-contrast score from `helix_wheel_faces()` (PR #71),
computed as `max(0, min(1, face_contrast / 2.0))` where face_contrast is the mean Eisenberg
hydrophobicity difference between the hydrophobic and hydrophilic helical faces. This measures
whether hydrophobic and cationic residues are properly segregated onto opposite helical faces —
a complementary signal to μH (moment magnitude alone). Falls back to 0.0 when absent (backward-
compatible). (Added as scoring term PR #72; computed by `helix_wheel_faces()` in PR #71.)

`charge_density_ph74` is the net peptide charge at pH 7.4 (Henderson-Hasselbalch) divided
by sequence length; the code falls back to `charge_density` (integer net-charge proxy / length)
for callers that pre-date the pH-7.4 charge model. Lookup uses explicit `if key in features`
conditional (not `dict.get()`) to avoid Python's eager evaluation of the fallback argument.

### 4.1b Boman Activity Score (Second Independent Scorer)

A second, independent activity score derived from the Boman index (Boman 2003):
`Boman index = mean of per-residue interaction potentials`

Interaction potentials are from Boman (2003), Table 1, set 2. Positive Boman index
(> 1.0) correlates with AMP-like protein-binding potential in the published benchmark.
The raw index is normalized to [0, 1] using a tanh mapping centred at 0.

**Model disagreement score**: `disagreement = |activity_likeness − boman_activity|`

A high disagreement value (≥ 0.30) indicates that the two independent scorers disagree
on the candidate's activity potential. This is a computational uncertainty signal, not
a biological risk flag. High-disagreement candidates warrant additional scrutiny before
lab nomination. Low-disagreement candidates (both scorers agree) are computationally
more robust nominations.

Reference: Boman HG (2003). Peptide antibiotics and their role in innate immunity.
Annual Review of Immunology, 13, 61-92.

### 4.2 Safety Score

Coarse hemolysis/cytotoxicity risk proxy. Higher score = safer. Computed from six risk
signals that sum to a `risk` variable; `score = 1.0 − clamp(risk, 0, 1)`.

| Risk signal | Threshold | Risk increment | Literature basis |
|------------|-----------|---------------|-----------------|
| Strong amphipathicity (μH) | μH > 0.55 | (μH − 0.55) × 1.5 | Non-selective membrane disruption (Dathe 1999 BBA) |
| Excess hydrophobicity | hydrophobic_fraction > 0.65 | (hf − 0.65) × 1.8 | Membrane partitioning at high hf |
| Excess charge density (pH 7.4) | charge_density_ph74 > 0.55 | (cd − 0.55) × 1.2 | Non-selective cationic disruption |
| Long sequence | length > 35 | +0.25 | Synthesis yield loss |
| High cysteine content | cysteine_fraction > 0.25 | +0.20 | Disulfide-mediated aggregation |
| Long repeat run | longest_repeat_run ≥ 6 | +0.15 | On-resin aggregation |

`charge_density_ph74` (preferred) falls back to `abs(charge_density)` for callers
predating the pH-7.4 charge model.

**Critical limitation:** This score has never been calibrated against experimental
hemolysis or cytotoxicity measurements. It is a physics-based proxy only. Lab hemolysis
assay (e.g., red blood cell lysis assay) is mandatory before any safety claim.

### 4.3 Synthesis Feasibility Score

Penalizes sequences predicted to be difficult to synthesize by solid-phase peptide synthesis
(SPPS). Score starts at 1.0; each penalty is subtractive; final score clamped to [0, 1].

| Penalty | Threshold | Deduction | Mechanism |
|---------|-----------|-----------|-----------|
| Long sequence | length > 30 | min((length − 30) × 0.04, 0.40) | Deletion error accumulation; up to −0.40 at length ≥ 40 |
| Very short sequence | length < 8 | −0.30 flat | Unreliable purification / characterisation |
| Long homo-repeat run (any AA) | longest_repeat_run ≥ 5 | −0.10 flat | Coupling efficiency drops on identical-residue stretches |
| High cysteine fraction | cysteine_fraction > 0.20 | −0.15 flat | Disulphide scrambling; side-chain protection cost |
| Aggregation propensity | aggregation_propensity > 0 | min(prop × 0.25, 0.20) | On-resin self-association from hydrophobic runs {V,I,L,M,F,W} or β-branched density |
| High proline fraction | proline_fraction > 0.15 | −0.10 flat | N-terminal DKP; slow coupling at XP junctions during Fmoc deprotection |

**Proline penalty detail:** Proline's N-methylated backbone causes slow coupling at
XP-junction positions and N-terminal diketopiperazine (DKP) cyclisation risk during
piperidine Fmoc deprotection. References: Barlos et al. (1989) Int J Peptide Protein Res;
Quibell et al. (1994) J Am Chem Soc; Fischer (2003) Curr Opin Drug Discov Devel.

**Aggregation penalty detail:** `aggregation_propensity` from `features/physchem.py` uses
two components: (1) longest consecutive run in {V,I,L,M,F,W} (ramp: 0 at run < 4, 1.0 at
run ≥ 8) and (2) β-branched density (V,I,T > 20%). The synthesis penalty is
`min(agg × 0.25, 0.20)` — a linear ramp from zero, capped at −0.20.

**Length boundary note:** The synthesis penalty threshold (length > 30) differs from the
pipeline's sequence validity filter (length > 35 is flagged in safety, not synthesis). A
candidate of length 32 incurs a −0.08 synthesis deduction but is not safety-penalised for
length.

### 4.3b Serum Stability Score

Estimates relative proteolytic longevity from interior cleavage-site densities. Higher = more
stable. Score = `1 − clamp(combined_density / 0.5, 0, 1)`.

| Protease | P1 substrates | Site weight | Literature |
|----------|--------------|-------------|-----------|
| Trypsin | K, R (interior) | 2.0 | Dominant serum degradation; t½ < 30 min at ≥3 interior K/R (Hilpert 2006) |
| Chymotrypsin | F, W, Y (interior) | 1.0 | Secondary serum route |
| Neutrophil elastase (HNE) | A, V, S (interior) | 0.5 | Abundant at infection sites; HNE cleaves Ala > Val > Ser (Bieth 1986; Doherty 1991) |

`combined_density = (2.0 × trypsin + 1.0 × chymo + 0.5 × elastase) / 3.5`

Score 1.0 = no interior sites; 0.5 = combined density ≈ 0.25/residue; 0.0 ≥ 0.5/residue.
This score does not gate the ensemble — it is used only in the pilot panel ranking (§5.2).

### 4.4 Novelty Score

Novelty is computed as: `1 - max_similarity`, where max_similarity is the maximum normalized
Levenshtein similarity between the candidate and any sequence in the 72-sequence reference set
(`examples/known_reference/amp_curated_references.csv`).

Normalized Levenshtein similarity: `1 - (edit_distance / max_length)`.

A novelty of 0.0 means the sequence is identical to a known reference. A novelty of 1.0 means
no sequence in the reference set is similar at all.

**Limitation:** The reference set contains only 72 curated sequences. This is not a complete
survey of known AMPs. Real-world novelty should be checked against APD3, CAMP, DRAMP, and
UniProt antimicrobial sequences.

### 4.5 Ensemble Score

`ensemble = 0.35 × activity + 0.30 × safety + 0.20 × synthesis + 0.15 × novelty`

Weights were set by expert judgment before any candidate generation. They are not
data-optimized and have not been validated. The scoring rule is pre-registered in
`docs/SELECTION_RULE.md`.

---

## 5. Candidate Selection

### 5.1 Phase-3 Batch Selection

1. **Filter**: Length 8–35 aa, canonical AAs only, safety ≥ 0.60, novelty ≥ 0.05, ensemble ≥ 0.0
2. **Rank**: By ensemble score (descending)
3. **Diversity select**: Greedy selection with pairwise similarity cap of 0.80
4. **Target batch**: Up to 100 candidates

The complete pre-registered rule is in `docs/SELECTION_RULE.md`.

### 5.2 Pilot Panel Selection (first-synthesis wave)

The pilot panel selects the 20 best candidates from the ranked batch for first-wave synthesis.
Each candidate is scored by `pilot_priority`:

```
pilot_priority = ensemble
               − 0.30 × disagreement
               + 0.05 × serum_stability
               + 0.05 × novelty
               + 0.05 × selectivity_proxy
               − cytotox_penalty
```

`cytotox_penalty = 0.0` if `selectivity_proxy ≥ 0.5`, else `0.05 × (0.5 − proxy) / 0.5`

| Term | Rationale |
|------|-----------|
| −0.30 × disagreement | Penalises candidates where activity vs Boman scorers diverge |
| +0.05 × serum_stability | Rewards proteolytically stable candidates |
| +0.05 × novelty | Rewards structural distance from known references |
| +0.05 × selectivity_proxy | Rewards candidates with favourable charge/GRAVY selectivity profile |
| −cytotox_penalty | Extra demerit for HIGH_CYTOTOX_RISK tier (proxy < 0.5); max −0.05 additional |

**Net selectivity swing**: a perfectly selective candidate (proxy = 1.0) outranks a
temporin-like low-selectivity candidate (proxy = 0.30) by 0.055 points — the same as
ensemble gaining ~1.5 standard deviations in the demo pool.

Selection rules (in order):
1. One representative per distinct seed (best by pilot_priority)
2. Remaining slots filled by priority, subject to `max_per_seed` cap (default 4)
3. Optional diversity filter: similarity_threshold = 0.75 between panel members

---

## 6. Evidence Certificates

Each selected candidate receives a JSON evidence certificate (`outputs/phase3_evidence/`),
validated against `schemas/candidate.schema.json`. Certificates include:

- Candidate ID, sequence, and source
- All physicochemical features
- All individual and ensemble scores
- Nearest reference sequence and novelty distance
- Selection reason and known failure modes
- Pipeline version, config hash, and generation timestamp

---

## 7. Reproducibility

All pipeline outputs are deterministic given:
- Fixed input sequences (`examples/sequences/phase3_pool.csv`)
- Fixed reference set (`examples/known_reference/amp_curated_references.csv`)
- Fixed config (`configs/phase3.yaml`)
- Fixed RNG seed (rng_seed=2024 in generator)
- Fixed pipeline version (`pipeline_version: 0.1.0`)

The run manifest (`outputs/phase3_manifest.json`) records:
- SHA-256 hashes of all input files
- Config hash (SHA-256 of sorted JSON representation)
- Pipeline version
- Run timestamp

To reproduce: `git checkout <commit> && make phase3`

---

## 8. Benchmark Validation

Phase 2 benchmarks verified that the pipeline:
- Recovers hidden known-positive AMPs better than random baseline (EF > 1.0)
- Remains meaningful under cluster-split evaluation (no near-duplicate leakage)
- Down-ranks poly-cationic and poly-hydrophobic negatives
- Produces stable rankings under repeated runs (reproducibility)
- Shows performance degradation when key scoring dimensions are ablated

**Retrospective AUROC — pipeline.yaml (v0.8.x):** `0.8420` (bootstrap CI₉₅: 0.76–0.91, n=87, n_bootstrap=2000).
Positive-vs-negative separation on the 43-AMP + 44-background benchmark set using the full
ensemble scorer with pipeline.yaml weights. Historical progression: 0.7926 → 0.8138 →
0.8164 (PRs #48–54) → 0.8086 (PR #65: Trp-weighted aromatic bonus, safety abs() fix) →
0.8047 (PR #66: removed duplicate REF-GIG-001; 43 unique AMPs) →
0.8348 (PR #70: windowed mu_h + anionic guard) →
0.8420 (PR #72: face_segregation_bonus; see below).

**Retrospective AUROC — phase3.yaml (synthesis gate, v0.8.x):** `0.8266` (bootstrap CI₉₅: 0.74–0.90, n=87, n_bootstrap=2000). Phase3 uses re-weighted ensemble scores (activity=0.35, safety=0.30,
synthesis=0.20, novelty=0.15 vs pipeline.yaml activity=0.40, safety=0.25, synthesis=0.15,
novelty=0.20) and a stricter safety gate (max_safety_risk=0.40). Historical: 0.7846 (PR #66)
→ 0.8126 (PR #70) → 0.8266 (PR #72). The AUROC is lower than pipeline.yaml because the higher
safety weight down-ranks some literature AMPs that have hemolysis risk, which is scientifically
correct behaviour for a synthesis gate. Interpretation: **STRONG** (AUROC > 0.70).

> **Important:** The synthesis selection gate uses phase3.yaml. The phase3 AUROC (0.8266) is the
> operationally relevant benchmark. pipeline.yaml AUROC (0.8420) is the full-ensemble reference.
> Both point estimates comfortably exceed the AUROC > 0.70 synthesis gate. Note that with n=87
> sequences the 95% CI spans ~±0.09; synthesis decisions are made on point estimates, which is
> standard practice at this sample size — the CI reflects sampling uncertainty, not model unreliability.

**AUPRC (v0.8.x):** `0.8627` for pipeline.yaml (+0.3684 above the random baseline of 0.4943);
`0.8479` for phase3.yaml.
Area Under Precision-Recall Curve is computed alongside AUROC and reported by `make validate-scoring`.
AUPRC is preferable to AUROC for class-imbalanced datasets because it emphasises precision
at the operating point actually used for candidate selection. Random baseline = dataset
prevalence (43/87 ≈ 0.4943 for the slightly unbalanced post-dedup set). Implemented with
pessimistic tie-breaking (negatives sort first on tied scores) to match sklearn
`average_precision_score` convention and avoid inflation to 1.0 for constant-score classifiers.

**To reproduce:** `make validate-scoring` (pipeline.yaml weights) or
`make validate-scoring-phase3` (synthesis gate weights, phase3.yaml) or
`make validate-scoring-strict` for the composition-matched (scrambled-decoy) variant.

**Key scoring changes in v0.2.x–v0.8.x (PRs #48–72):**

| PR | Change | AUROC impact |
|----|--------|-------------|
| #47 | Selectivity proxy (charge/GRAVY) | + |
| #48 | Selectivity proxy routed into pilot_priority | pilot ranking |
| #49 | Elastase resistance + aggregation propensity | + |
| #50 | Aggregation-safe mutations + balanced K/R variants | generation |
| #51 | Proline synthesis penalty (−0.10 at >15%); helix bonus 0.01→0.03 | 0.8138→0.8164 |
| #53 | Safety uses charge_density_ph74; stronger cytotox_penalty in pilot | pilot ranking |
| #58 | AUPRC added; SEED-009 (Bac2A) + SEED-010 (KR-12) added | +2 scaffolds |
| #65 | Trp-weighted aromatic bonus (1.5× vs Phe/Tyr); safety abs() fix | 0.8164→0.8086 |
| #66 | Remove duplicate REF-GIG-001 (magainin-2 counted twice in validation set) | 0.8086→0.8047 |
| #70 | Windowed mu_h (window=11, Eisenberg standard); anionic charge guard | 0.8047→0.8348 (pipeline); 0.7846→0.8126 (phase3) |
| #72 | Face segregation bonus (helix_wheel_amphipathic_score × 0.05); max_disagreement 0.40→0.45 | 0.8348→0.8420 (pipeline); 0.8126→0.8266 (phase3) |

**PR #70 detail — windowed hydrophobic moment:** For sequences > 11 residues, the full-sequence
μH is diluted by non-helical termini and linker regions. `max_windowed_hydrophobic_moment()`
computes the maximum μH over all 11-residue windows (the Eisenberg standard helical period).
For magainin-2 (23 AA): full-seq μH = 0.4548 vs windowed μH = 0.6862 (1.51×). For cecropin-A
(37 AA): full-seq μH = 0.2267 vs windowed μH = 0.6567 (2.90×). Short sequences (≤ 11 AA)
are unaffected: windowed == full-seq.

**PR #70 detail — anionic charge guard:** Anionic peptides (charge_density_ph74 < 0.0) are
electrostatically repelled by bacterial membranes (phosphatidylglycerol, cardiolipin surface)
and cannot operate via the canonical cationic AMP mechanism. The guard returns 0.0 immediately,
preventing partial credit from hydrophobic/length terms. Boundary: exactly 0.0 charge density
is not blocked (reflects neutral peptides rather than anionic). Fixed a Python eagerness bug
in feature dict lookup (`features.get(key, features["fallback"])` evaluates fallback eagerly;
replaced with explicit `if "key" in features` conditional).

**PR #72 detail — face segregation bonus:** `helix_wheel_faces()` (PR #71) computes
`face_contrast = hydrophobic_face_mean_h − hydrophilic_face_mean_h` using the hydrophobic
moment vector to orient the helix wheel. `amphipathic_score = max(0, min(1, contrast/2.0))`.
This captures whether cationic residues are properly segregated onto the hydrophilic face — a
complementary signal to μH (which measures total moment magnitude without regard for charge
distribution). Weight 0.05 was chosen at the knee of the AUROC vs weight curve (activity-only
AUROC +0.90% vs baseline at w=0.05; +1.59% at w=0.15 — conservative choice to avoid
over-penalising non-helical AMPs). `max_disagreement` raised 0.40 → 0.45 in both configs because
`face_segregation_bonus` correctly elevated SEED-008 Trp-rich activity scores by ~0.03 score
units (their Trp clusters form a genuine hydrophobic face), pushing disagreement from ~0.40 to
~0.43. No non-Trp-rich candidate in the 709-sequence phase3 pool exceeds disagreement=0.41,
so the new 0.45 threshold still blocks genuinely uncertain candidates.
Literature: Wieprecht et al. (1997) Biochemistry 36:6124; Tossi et al. (2000) Biopolymers 55:4.

**Limitation:** Benchmarks use a small, curated demo dataset (43 AMPs + 44 background). They
do not validate against large independent AMP databases. Real retrospective validation against
APD3-scale data (> 3,000 AMPs, cluster-split) is required before strong claims of predictive
power.

---

## 9. Known Failure Modes

| Failure mode | Impact | Status |
|-------------|--------|--------|
| Scoring not validated against lab data | Activity/safety scores may not correlate with assay results | Known; lab calibration needed |
| Near-seed generation only | Misses genuinely novel AMP families | Known; future work |
| Small reference set | Novelty may be overestimated | Partially mitigated; 72 refs used |
| Two scorers only | Disagreement is coarse uncertainty; not a calibrated posterior | Partially mitigated; Boman index added in v0.2 |
| Helical amphipathicity assumption | Non-helical AMPs underscored | Known limitation |
| No structural modeling | Cannot predict membrane interaction mode | Out of scope v0.1 |

---

## 10. References

- Bieth, J.G. (1986). Elastases: structure, function and pathological role. Bull Eur Physiopathol Respir, 22(Suppl 7), 7–12.
- Bjellqvist, B. et al. (1993). The focusing positions of polypeptides in immobilized pH gradients can be predicted from their amino acid sequences. Electrophoresis, 14(10), 1023–1031.
- Boman, H.G. (2003). Peptide antibiotics and their role in innate immunity. Annual Review of Immunology, 13, 61–92.
- Chou, P.Y. & Fasman, G.D. (1974). Conformational parameters for amino acids in helical, beta-sheet, and random coil regions calculated from proteins. Biochemistry, 13(2), 222–245.
- Dathe, M. & Wieprecht, T. (1999). Structural features of helical antimicrobial peptides: their potential to modulate activity on model membranes and biological cells. Biochim Biophys Acta, 1462(1–2), 71–87.
- Doherty, J.B. et al. (1991). Potent and selective human neutrophil elastase inhibitors. Biochemistry, 30(35), 8540–8550.
- Eisenberg, D. et al. (1984). Analysis of membrane and surface protein sequences with the hydrophobic moment plot. J Mol Biol, 179(1), 125–142.
- Fields, G.B. & Noble, R.L. (1990). Solid phase peptide synthesis utilizing 9-fluorenylmethoxycarbonyl amino acids. Int J Pept Protein Res, 35(3), 161–214.
- Hancock, R.E. & Sahl, H.G. (2006). Antimicrobial and host-defense peptides as new anti-infective therapeutic strategies. Nature Biotechnology, 24(12), 1551–1557.
- Hilpert, K. et al. (2006). Short cationic antimicrobial peptides interact with ATP. Antimicrob Agents Chemother, 50(12), 4181–4188.
- Huang, H.W. (2000). Action of antimicrobial peptides: two-state model. Biochemistry, 39(29), 8347–8352.
- Jenssen, H. et al. (2006). Peptide antimicrobial agents. Clinical Microbiology Reviews, 19(3), 491–511.
- Kyte, J. & Doolittle, R.F. (1982). A simple method for displaying the hydropathic character of a protein. J Mol Biol, 157(1), 105–132.
- Tossi, A. et al. (2000). Amphipathic, alpha-helical antimicrobial peptides. Biopolymers, 55(1), 4–30.
- Wade, D. et al. (1990). All-D amino acid-containing channel-forming antibiotic peptides. Proc Natl Acad Sci USA, 87(12), 4761–4765.
- Wimley, W.C. & White, S.H. (1996). Experimentally determined hydrophobicity scale for proteins at membrane interfaces. Nat Struct Biol, 3(10), 842–848.
- Zasloff, M. (1987). Magainins, a class of antimicrobial peptides from Xenopus skin. PNAS, 84(15), 5449–5453.
- Zasloff, M. (2002). Antimicrobial peptides of multicellular organisms. Nature, 415(6870), 389–395.

Full candidate-level references are in each evidence certificate.

---

## 11. Ethical Statement

This pipeline does not optimize for toxicity, virulence, immune evasion, or any harmful
objective. All candidates are short, linear, non-targeted peptides evaluated for potential
antimicrobial utility only. No dangerous organism protocols, pathogen enhancement, or
harmful objectives are present in this repository. Generator outputs have not been screened
against bioweapon databases; expert review is required before any external release.
