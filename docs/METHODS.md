# OpenAMP Foundry — Methods Appendix

**Version:** 0.1.0  
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

A heuristic score approximating AMP-like properties, computed from net_charge_proxy,
hydrophobic_fraction, hydrophobic_moment, and length. Weights are not optimized; they
encode biochemical priors only. Score range: [0, 1].

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

Penalizes sequences with properties associated with hemolysis risk or synthesis difficulty:

| Risk signal | Threshold | Penalty |
|------------|-----------|---------|
| Excess hydrophobicity | hydrophobic_fraction > 0.65 | multiplicative reduction |
| Excess charge density | charge_density > 0.55 | multiplicative reduction |
| High cysteine content | cysteine_fraction > 0.25 | multiplicative reduction |
| Long sequence | length > 35 | multiplicative reduction |
| Long repeat run | longest_repeat_run ≥ 6 | multiplicative reduction |

**Critical limitation:** This safety score has never been calibrated against experimental
hemolysis or cytotoxicity measurements. It is a physics-based proxy only. Lab hemolysis
assay (e.g., red blood cell lysis assay) is mandatory before any safety claim.

### 4.3 Synthesis Feasibility Score

Penalizes sequences that are predicted to be difficult to synthesize by solid-phase peptide
synthesis (SPPS):

| Property | Concern |
|----------|---------|
| High cysteine fraction | Disulfide bridge complications |
| High proline fraction | Coupling difficulty |
| Very long sequences | Stepwise synthesis yield loss |
| Non-canonical amino acids | Not applicable (filtered upstream) |

### 4.4 Novelty Score

Novelty is computed as: `1 - max_similarity`, where max_similarity is the maximum normalized
Levenshtein similarity between the candidate and any sequence in the 45-sequence reference set
(`examples/known_reference/amp_curated_references.csv`).

Normalized Levenshtein similarity: `1 - (edit_distance / max_length)`.

A novelty of 0.0 means the sequence is identical to a known reference. A novelty of 1.0 means
no sequence in the reference set is similar at all.

**Limitation:** The reference set contains only 45 curated sequences. This is not a complete
survey of known AMPs. Real-world novelty should be checked against APD3, CAMP, DRAMP, and
UniProt antimicrobial sequences.

### 4.5 Ensemble Score

`ensemble = 0.35 × activity + 0.30 × safety + 0.20 × synthesis + 0.15 × novelty`

Weights were set by expert judgment before any candidate generation. They are not
data-optimized and have not been validated. The scoring rule is pre-registered in
`docs/SELECTION_RULE.md`.

---

## 5. Candidate Selection

1. **Filter**: Length 8–35 aa, canonical AAs only, safety ≥ 0.60, novelty ≥ 0.05, ensemble ≥ 0.0
2. **Rank**: By ensemble score (descending)
3. **Diversity select**: Greedy selection with pairwise similarity cap of 0.80
4. **Target batch**: Up to 100 candidates

The complete pre-registered rule is in `docs/SELECTION_RULE.md`.

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

**Limitation:** Benchmarks use a small, curated demo dataset. They do not validate against
large independent AMP databases. Real retrospective validation against APD3-scale data is
required before strong claims of predictive power.

---

## 9. Known Failure Modes

| Failure mode | Impact | Status |
|-------------|--------|--------|
| Scoring not validated against lab data | Activity/safety scores may not correlate with assay results | Known; lab calibration needed |
| Near-seed generation only | Misses genuinely novel AMP families | Known; future work |
| Small reference set | Novelty may be overestimated | Partially mitigated; 45 refs used |
| Two scorers only | Disagreement is coarse uncertainty; not a calibrated posterior | Partially mitigated; Boman index added in v0.2 |
| Helical amphipathicity assumption | Non-helical AMPs underscored | Known limitation |
| No structural modeling | Cannot predict membrane interaction mode | Out of scope v0.1 |

---

## 10. References

- Eisenberg, D. et al. (1984). Analysis of membrane and surface protein sequences with the hydrophobic moment plot. J Mol Biol, 179(1), 125-142.
- Kyte, J. & Doolittle, R.F. (1982). A simple method for displaying the hydropathic character of a protein. J Mol Biol, 157(1), 105-132.
- Wimley, W.C. & White, S.H. (1996). Experimentally determined hydrophobicity scale for proteins at membrane interfaces. Nat Struct Biol, 3(10), 842-848.
- Zasloff, M. (1987). Magainins, a class of antimicrobial peptides from Xenopus skin. PNAS, 84(15), 5449-5453.

Full candidate-level references are in each evidence certificate.

---

## 11. Ethical Statement

This pipeline does not optimize for toxicity, virulence, immune evasion, or any harmful
objective. All candidates are short, linear, non-targeted peptides evaluated for potential
antimicrobial utility only. No dangerous organism protocols, pathogen enhancement, or
harmful objectives are present in this repository. Generator outputs have not been screened
against bioweapon databases; expert review is required before any external release.
