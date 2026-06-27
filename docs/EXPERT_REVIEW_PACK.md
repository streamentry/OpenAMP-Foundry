# OpenAMP Foundry — Expert Review Pack

**Phase 3 Candidate Batch**  
**Pipeline version:** 0.1.0 (v0.2 scorer update)  
**Generated:** 2026-06-27  
**Batch ID:** See `outputs/phase3_manifest.json`

---

## Purpose of This Document

This document is prepared for review by a qualified microbiology, peptide chemistry, or
infectious disease expert prior to any wet-lab expenditure. It summarises the computational
candidate nomination process, the selection rationale, and the recommended next steps.

**The expert reviewer is asked to:**
1. Evaluate whether the candidate selection methodology is scientifically credible.
2. Identify any obvious problems the computational pipeline may have missed.
3. Advise on which candidates (if any) are worth synthesising.
4. Recommend appropriate assay types and target organisms.
5. Flag any safety or dual-use concerns.

---

## Computational Disclaimer

All scores in this document are heuristic physicochemical proxies. They are NOT validated
biological predictors. No antimicrobial activity has been demonstrated in vitro or in vivo.
Do not describe any candidate as an antibiotic, drug, cure, therapy, or proven antimicrobial
without experimental evidence. The lab is the judge.

---

## 1. Overview of the Pipeline

The OpenAMP Foundry pipeline applies a six-stage scoring system to candidate sequences:

| Stage | Method | What it measures |
|-------|--------|-----------------|
| Activity-likeness | Physicochemical heuristics | Charge, hydrophobicity, amphipathicity, length |
| Boman activity | Boman (2003) index normalized | Per-residue interaction potential; complements activity heuristic |
| Model disagreement | \|activity − boman_activity\| | Scorer consensus: low = robust, high = uncertain |
| Safety (toxicity proxy) | Physicochemical risk flags | Hemolysis-correlated excess hydrophobicity, charge density, repeats |
| Synthesis feasibility | Composition and length filter | Cysteine content, proline content, repeat runs, length |
| Novelty | Levenshtein distance | Sequence divergence from 45 known AMP references |
| Ensemble | Weighted sum | activity×0.35 + safety×0.30 + synthesis×0.20 + novelty×0.15 |

**Pipeline configuration:** `configs/phase3.yaml`  
**Selection rule:** `docs/SELECTION_RULE.md` (locked before generation)  
**Full benchmark methodology:** `docs/BENCHMARKING.md`

**Key evidence level:** These are Level 0–2 evidence scores (syntax validity, reproducible features,
transparent heuristics). They have not been validated against lab measurements. Lab assay
(Level 5) is the required next gate.

---

## 2. Reference Set

Novelty was scored against **45 known antimicrobial peptides** drawn from published literature
(see `examples/known_reference/amp_curated_references.csv`). Families represented:

- Magainin and pexiganan analogs (Zasloff 1987, Ge 1999)
- Buforin family (Kim 1996, Park 2000)
- Indolicidin and analogs (Selsted 1992)
- Temporin family (Mangoni 2001, Simmaco 1996)
- Aurein family (Rozek 2000)
- Cecropin family (Steiner 1981, Hultmark 1980)
- Cathelicidin-related short sequences
- Melittin (as hemolysis positive control reference)

**Assessment:** Candidates with novelty < 0.10 against this reference set are near-duplicates
of known AMPs and should be deprioritised. Novelty ≥ 0.30 indicates meaningful divergence from
the known AMP landscape.

---

## 3. Generation Method

Candidates were produced by conservative amino-acid substitutions on 5 template seeds:

| Seed | Sequence | Family |
|------|----------|--------|
| SEED-001 | KWKLFKKIGAVLKVL | Magainin-like |
| SEED-002 | GIGKFLHSAKKFGKAFVGEIMNS | Cecropin/Magainin-like |
| SEED-003 | RRWQWRMKKLG | Cationic tryptophan-rich |
| SEED-004 | FLPLIGRVLSGIL | Temporin-like |
| SEED-005 | KRLFKKIGSALKFL | Hybrid cationic-hydrophobic |

Substitutions were restricted to physicochemically conservative groups (cationic→cationic,
hydrophobic→hydrophobic, etc.) to preserve the amphipathic balance of the templates.

**Reviewer note:** This is an intentionally conservative generation strategy. It explores the
near-neighbourhood of known AMP families. It does NOT explore truly novel sequence space.
Future cycles should incorporate independent sequence generation (e.g. protein language models
or Bayesian optimization) to achieve more radical novelty.

---

## 4. Batch Statistics

| Metric | Value |
|--------|-------|
| Sequences generated | 383 |
| Sequences passing all filters | 89 |
| Sequence length range | 11–14 aa |
| Mean ensemble score | 0.781 |
| Mean predicted activity | 0.839 |
| Mean predicted safety | 1.000 |
| Mean synthesis feasibility | 1.000 |
| Mean novelty vs reference set | 0.172 |
| Diversity clusters (threshold 0.80) | 32 |
| Singleton clusters | 13 (40.6%) |
| Mean Boman activity score | 0.503 |
| Mean scorer disagreement | 0.311 |
| High consensus (disagreement <0.20) | 1 |
| Uncertain (disagreement ≥0.30) | 48 |

**Reviewer alert — Safety scores:** Mean safety = 1.0 because ALL selected candidates passed
the safety filter (max_safety_risk = 0.40). This is because the conservative substitution
generator preserves balanced charge/hydrophobicity. This looks good computationally, but does
not replace wet-lab hemolysis and cytotoxicity assays.

**Reviewer alert — Scorer disagreement:** The mean disagreement between the activity-likeness
heuristic and the Boman index second scorer is 0.311. This is expected: the activity scorer
rewards amphipathic charge/hydrophobicity balance (good for membrane disruption), while the
Boman index penalizes hydrophobic residues as lower interaction potential. The disagreement is
scientifically honest — these candidates are predicted AMPs through amphipathic mechanisms but
have moderate protein-binding potential by the Boman criterion. Candidates with higher Boman
scores should be given extra weight in expert review.

**Reviewer alert — Cluster concentration:** 59% of candidates fall within multi-member clusters,
meaning significant chemical similarity within the batch. Only ~13 candidates are sequence-isolated
singletons. The expert should advise whether this diversity level is adequate for meaningful assay.

---

## 5. Top 20 Candidates by Ensemble Score (with Dual-Scorer Columns)

> These candidates passed all computational filters and were selected by greedy diversity.
> Rankings are provisional and may change with improved scoring in future pipeline versions.
> **Dis** = scorer disagreement; lower is more robust (dual-scorer consensus).

| Rank | Candidate ID | Sequence | Ens | Activity | Boman | Dis | Safety | Novelty | Len |
|------|-------------|----------|-----|----------|-------|-----|--------|---------|-----|
| 1 | SEED-005_VAR_049 | KRLFKKIPSALKFF | 0.880 | 0.885 | 0.485 | 0.400 | 1.000 | 0.467 | 14 |
| 2 | SEED-005_VAR_009 | KRFFKKIGSALKFA | 0.877 | 0.878 | 0.508 | 0.370 | 1.000 | 0.467 | 14 |
| 3 | SEED-005_VAR_063 | KRLFRKIGSALKFV | 0.874 | 0.867 | 0.503 | 0.365 | 1.000 | 0.467 | 14 |
| 4 | SEED-005_VAR_058 | KRLFKKVGSALRFL | 0.871 | 0.861 | 0.503 | 0.358 | 1.000 | 0.467 | 14 |
| 5 | SEED-005_VAR_023 | KRLFKKIGRALKFL | 0.870 | 0.913 | 0.537 | 0.376 | 1.000 | 0.333 | 14 |
| 6 | SEED-005_VAR_061 | KRLFKRLGSALKFL | 0.868 | 0.853 | 0.497 | 0.355 | 1.000 | 0.467 | 14 |
| 7 | SEED-005_VAR_068 | KRLMKKIGSAIKFL | 0.856 | 0.818 | 0.519 | 0.299 | 1.000 | 0.467 | 14 |
| 8 | SEED-005_VAR_013 | KRLAKHIGSALKFL | 0.855 | 0.814 | 0.480 | 0.334 | 1.000 | 0.467 | 14 |
| 9 | SEED-005_VAR_002 | HRLIKKIGSALKFL | 0.849 | 0.813 | 0.457 | 0.356 | 1.000 | 0.429 | 14 |
| 10 | SEED-003_VAR_027 | RRWQWRFKRLG | 0.839 | 0.890 | 0.532 | 0.358 | 1.000 | 0.182 | 11 |
| 11 | SEED-003_VAR_045 | RRWQYRIKKLG | 0.834 | 0.877 | 0.572 | 0.305 | 1.000 | 0.182 | 11 |
| 12 | SEED-003_VAR_020 | RRWQWHIKKLG | 0.832 | 0.870 | 0.480 | 0.390 | 1.000 | 0.182 | 11 |
| 13 | SEED-003_VAR_014 | RRFQWRMRKLG | 0.831 | 0.867 | 0.579 | 0.288 | 1.000 | 0.182 | 11 |
| 14 | SEED-003_VAR_017 | RRWNWRMRKLG | 0.829 | 0.862 | 0.559 | 0.303 | 1.000 | 0.182 | 11 |
| 15 | SEED-005_VAR_047 | KRLFKKIGSVLKML | 0.829 | 0.825 | 0.501 | 0.324 | 1.000 | 0.267 | 14 |
| 16 | SEED-003_VAR_048 | RRWSWHMKKLG | 0.828 | 0.860 | 0.493 | 0.367 | 1.000 | 0.182 | 11 |
| 17 | SEED-003_VAR_003 | KRWQWRIKKLG | 0.828 | 0.859 | 0.547 | 0.311 | 1.000 | 0.182 | 11 |
| 18 | SEED-003_VAR_049 | RRWSWRMHKLG | 0.828 | 0.859 | 0.493 | 0.365 | 1.000 | 0.182 | 11 |
| 19 | SEED-003_VAR_051 | RRWTWRMKKAG | 0.828 | 0.858 | 0.592 | 0.266 | 1.000 | 0.182 | 11 |
| 20 | SEED-003_VAR_042 | RRWQWRMRKLP | 0.828 | 0.858 | 0.559 | 0.299 | 1.000 | 0.182 | 11 |

Full list: `outputs/phase3_report.md`  
Machine-readable details: `outputs/phase3_batch_pack.json`  
Evidence certificates: `outputs/phase3_evidence/` (89 selected, all schema-validated)

**Reviewer priority note:** The SEED-003 family (tryptophan-rich 11-mers) has higher Boman
activity scores and lower disagreement than SEED-005 (14-mers), suggesting it should be prioritised
for synthesis. Rank 19 (RRWTWRMKKAG) has the highest Boman score among the top-20 (0.592) with
only moderate disagreement (0.266).

---

## 6. Reviewer Questions

Please advise on the following:

### 6.1 Scientific credibility
- [ ] Is the physicochemical scoring approach defensible for pre-screening short AMPs?
- [ ] Is the novelty threshold (≥ 0.05 against 45 known AMP references) meaningful?
- [ ] Does the diversity selection (max pairwise similarity 0.80) provide adequate batch diversity?
- [ ] Is the Boman index (2003) a defensible second scorer for this class of peptides?
- [ ] Is the mean scorer disagreement (0.311) consistent with what you would expect for helical AMPs?

### 6.2 Candidate quality
- [ ] Do any of the top-20 candidates have obvious structural or sequence-level problems?
- [ ] Are there specific sequences in the batch you would prioritise or deprioritise?
- [ ] Is 11–14 aa the right length range, or should we explore longer candidates?
- [ ] Do the SEED-003 tryptophan-rich 11-mers look more promising than the SEED-005 14-mers?

### 6.3 Assay recommendations
- [ ] Which assay types are most appropriate for initial screening? (Suggested: MIC, hemolysis)
- [ ] Which bacterial strains/organisms should be tested against?
- [ ] What constitutes a meaningful positive result? (e.g. MIC ≤ 8 µg/mL)
- [ ] How many candidates can reasonably be tested in a first-round assay?
- [ ] Do you have a preferred CRO or academic partner for peptide assays?

### 6.4 Safety and dual-use
- [ ] Are any sequences potentially concerning from a biosafety perspective?
- [ ] Are there any concerns about these sequences being misused?

---

## 7. Recommended Next Steps

Before any candidate proceeds to synthesis or assay:

1. **Expert sign-off**: A qualified reviewer completes section 6 above.
2. **Synthesis plan**: A peptide chemist reviews feasibility and recommends synthesis vendor.
3. **Target organism selection**: Microbiologist selects appropriate test organisms.
4. **Protocol pre-registration**: Assay protocol and pass/fail criteria locked before synthesis.
5. **Negative controls**: Known inactive sequences (e.g. scrambled versions) included in assay.
6. **Ethical and regulatory check**: PI confirms no IRB, ITAR, dual-use, or export-control issues.
7. **Pilot assay**: Small pilot (top 5–10 candidates by Boman+activity consensus) before full batch.

**Suggested pilot candidates (highest Boman × lowest disagreement):**

| Priority | Candidate ID | Sequence | Boman | Dis | Rationale |
|----------|-------------|----------|-------|-----|-----------|
| 1st | SEED-003_VAR_051 | RRWTWRMKKAG | 0.592 | 0.266 | Highest Boman among top-20, low disagreement |
| 2nd | SEED-003_VAR_014 | RRFQWRMRKLG | 0.579 | 0.288 | Strong Boman, low disagreement |
| 3rd | SEED-003_VAR_045 | RRWQYRIKKLG | 0.572 | 0.305 | Good Boman, 11-mer |
| 4th | SEED-003_VAR_003 | KRWQWRIKKLG | 0.547 | 0.311 | Good Boman, varied flanking residue |
| 5th | SEED-005_VAR_023 | KRLFKKIGRALKFL | 0.537 | 0.376 | Highest activity in batch (0.913) |

---

## 8. Pipeline Limitations (Required Disclosure)

The expert reviewer must be aware of these limitations:

| Limitation | Impact |
|-----------|--------|
| Level 0–2 evidence only | Scores are physicochemical heuristics, not validated ML predictions |
| Two scorers only | Boman index added as second scorer; disagreement available; no ML predictor yet |
| High mean disagreement (0.311) | Scorers model AMP activity by different mechanisms; consensus is weak for this batch |
| Novelty vs. 45 references only | Novel against this reference set does not mean novel against all known AMPs |
| Conservative generation only | Near-seed variants; genuinely novel families not explored |
| No structural prediction | No secondary structure, membrane interaction, or 3D modeling |
| Amphipathicity is helical-only | Assumes helix; β-sheet or other motifs not modeled |
| Safety proxy is not validated | The pipeline has never been calibrated against hemolysis data |
| Selection is single-objective | No multi-objective Pareto optimization; ensemble weights are heuristic |

---

## Contact

This document is produced by the OpenAMP Foundry computational pipeline.  
For human contact, see the repository README for contributor information.  
All decisions about synthesis, assay, or publication require human expert authorization.

**No candidate may be synthesised or sent to any external party without qualified expert review
and explicit human approval.**
