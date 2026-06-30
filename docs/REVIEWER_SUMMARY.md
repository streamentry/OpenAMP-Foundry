# OpenAMP Foundry — Reviewer Summary

**Pipeline:** v0.5.x | **Benchmark:** AUROC 0.7832 (95 AMP + 96 decoy, n=191) | **Panel:** 20 candidates, 7 families

---

## What This Is

A reproducible, safety-constrained computational pipeline for discovering novel antimicrobial
peptide families. This document is a 2-page summary for expert reviewers (microbiology, peptide
chemistry, infectious disease) to evaluate before wet-lab expenditure.

---

## Pipeline

| Stage | Method |
|-------|--------|
| Candidate generation | Template-based mutagenesis from 7 seed families |
| Activity scoring | Physicochemical heuristics (charge pH 7.4, hydrophobicity, amphipathicity, helix-wheel face segregation, Trp aromatic bonus) |
| Safety gate | Risk flags for hemolysis, cytotoxicity, aggregation |
| Selection | Multi-term priority: ensemble − 0.30×disagreement + 0.05×stability + 0.05×novelty + 0.05×selectivity |
| QC | Synthesis difficulty, DKP/pyroglutamate/Met oxidation/Trp photolability/Pro-rich intracellular flags |

## Benchmark

| Metric | Value |
|--------|-------|
| AUROC (expanded) | 0.7832 (CI₉₅: 0.72–0.84, n=191) |
| Phase3 gate AUROC | 0.7448 (STRONG, >0.70) |
| AUPRC | 0.8164 |
| Benchmark composition | 95 public-domain AMPs (12 taxonomic classes) + 96 composition-matched decoys |
| Original demo set | 0.8420 on 43+44 (historical baseline only) |

**Blind spot confirmed:** Melittin scores Safety=1.0 despite strong hemolysis — hemolysis
assay is mandatory for all candidates.

---

## Pilot Panel — 20 Candidates, 7 Families

| Family | Scaffold | n | Novelty type | Publishable novelty? | Key risk |
|--------|----------|:-:|--------------|:--------------------:|----------|
| SEED-001 | Magainin-1 | 1 | Positive control (86.7% to seed) | **No** — assay anchor | None (known active) |
| SEED-003 | Cationic Trp helix | 2 | KNOWN_VARIANT (81.8% to RRWQWRMKKLG) | **No** — SAR only | Serum stability 0.38 (11 AA; model may underestimate) |
| SEED-005 | Cecropin-magainin hybrid | 1 | CLOSE_RELATIVE (60%) | **Borderline** | Safety 0.845 (lowest in panel) |
| SEED-006 | Mastoparan-X (wasp venom) | 4 | NOVEL (< 40%) | **Yes** | Mast-cell degranulation |
| SEED-007 | Bombolitin-II (bumblebee) | 4 | NOVEL (< 38%) | **Yes** | Met oxidation at position 6 |
| SEED-008 | Puroindoline-a Trp-rich | 4 | NOVEL (< 33%) | **Yes** | DKP risk (FP N-terminus), Trp photolability |
| SEED-009 | Bac2A proline-rich | 4 | NOVEL (< 35%) | **Yes** | Intracellular target — requires RPMI-1640 assay |

**Broad novelty check (72-AMP reference):** 16/20 NOVEL, 3 KNOWN_VARIANT, 1 CLOSE_RELATIVE.

---

## Recommended Assay Protocol

1. **Serum stability triage** (all 20): 50% human serum, 0/30/60/120 min, HPLC quantification
2. **MIC screen** (top candidates): Broth microdilution, E. coli ATCC 25922, S. aureus ATCC 29213, MRSA USA300
3. **Hemolysis** (HC50): hRBCs, 1–512 µg/mL
4. **SEED-009 special**: Parallel RPMI-1640 + MHB assay (proline-rich mechanism requires cell
   penetration; MHB alone underestimates activity; Krizsan et al. 2014)

## Key Safety Pre-cautions

- All candidates are short synthetic peptides — standard BSL-2 handling adequate
- No disulfide-constrained, no lipopeptide, no toxin-directed candidates
- No pathogen-enhancing sequences in panel
- Pre-registered assay protocol locked before synthesis (`docs/ASSAY_PREREGISTRATION.md`)

---

## What This Pipeline Cannot Do (Known Limitations)

| Limitation | Impact |
|------------|--------|
| AUROC 0.7832 — 22% of benchmark pairs misranked | ~1 in 5 candidate ranking decisions are wrong; wet-lab is the judge |
| No 3D structure or docking | Helical assumption may misclassify non-helical mechanisms |
| Near-seed generation only | Novel sequence space not explored by de novo generation |
| Melittin safety blind spot | Hemolysis must be assayed — confirmed quantitatively: safety scorer detection AUROC=0.3844 on 14 hemolytic vs 21 selective AMPs (v0.5.9 selectivity benchmark) |
| No external predictor ensemble yet | CAMPR4/AMPScanner/dbAMP/AntiCP2/Macrel web submission checklist exists at `outputs/external_predict_checklist.md` but results not yet obtained |
| Probability table uncalibrated | All "P(≥1 active) ≈ 92–97%" statements are upper bounds; honest estimate 55–80% for any hit, 35–60% for novel family |

---

## Verdict Template for Reviewers

> **Computational quality:** Pipeline is well-engineered, reproducible, safety-aware.
> The expanded benchmark (95+96) is a meaningful improvement over the original demo set.
> **Recommendation:** The 20-candidate panel is worth a small Wave 1 synthesis batch
> (priority: SEED-007, SEED-008, SEED-009 novel families). Pre-register the assay protocol.
> **Caveat:** All probabilities above are unvalidated. The lab is the judge.

---

*Full docs: ASSAY_PREREGISTRATION.md, WET_LAB_HANDOFF.md, WET_LAB_PROBABILITY.md,
EXPERT_REVIEW_PACK.md, DISCOVERY_PREDICTION.md, NOVELTY_BROAD_CHECK.md, NOVELTY_CHECKLIST.md,
GOLD_STANDARD_CALIBRATION.md in `docs/`.*
