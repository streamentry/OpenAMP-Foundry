# Broad Novelty Check — Pilot Panel vs Curated AMP Database

> Generated: 2026-06-28T16:35:23.456115+00:00  
> Panel: outputs/pilot_panel.csv  
> Reference database: examples/known_reference/amp_curated_references.csv (72 unique sequences)  
> Thresholds: KNOWN_VARIANT ≥ 70%, CLOSE_RELATIVE ≥ 50%

## Purpose

The standard pipeline novelty score compares candidates against ~45 seed sequences.
This report extends the comparison to the curated AMP reference database to detect
near-copies of published AMPs that the seed-based novelty score may miss.

## Summary

| Category | Count | Description |
|---|:---:|---|
| KNOWN_VARIANT | 3 | ≥70% similar to a known published AMP |
| CLOSE_RELATIVE | 1 | 50%–70% similar to a known AMP |
| NOVEL | 16 | <50% similar — no close match in reference database |
| **Total** | **20** | |

## Per-Candidate Results

| Rank | Candidate | Sequence | Seed | Ensemble | Seed-Novelty | Broad-Sim | Best-Match | Category |
|--:|---|---|---|:---:|:---:|:---:|---|---|
| 1 | SEED-009_VAR_033 | `RRLPRPGYMPRP` | SEED-009 | 0.807 | 0.692 | 0.308 | REF-TRP-001 (tryptophan_rich_cathelicidin) | ✓ NOVEL |
| 2 | SEED-009_VAR_027 | `RRLPRGPYLPKP` | SEED-009 | 0.808 | 0.692 | 0.308 | REF-TRP-001 (tryptophan_rich_cathelicidin) | ✓ NOVEL |
| 3 | SEED-007_VAR_009 | `IKFTTMLRKLG` | SEED-007 | 0.849 | 0.727 | 0.273 | REF-RRW-001 (tachyplesin_like) | ✓ NOVEL |
| 4 | SEED-007_VAR_001 | `AKITTMLKKLG` | SEED-007 | 0.824 | 0.636 | 0.364 | REF-RRW-001 (tachyplesin_like) | ✓ NOVEL |
| 5 | SEED-007_VAR_018 | `IKISTMLKKAG` | SEED-007 | 0.815 | 0.647 | 0.353 | REF-PIS-001 (piscidin) | ✓ NOVEL |
| 6 | SEED-009_VAR_039 | `RRLPRPPYIPRG` | SEED-009 | 0.796 | 0.650 | 0.350 | REF-PYR-001 (pyrrhocoricin) | ✓ NOVEL |
| 7 | SEED-009_VAR_017 | `RRLGRPPYLGRP` | SEED-009 | 0.798 | 0.647 | 0.353 | REF-BUF-002 (buforin_ii) | ✓ NOVEL |
| 8 | SEED-007_VAR_035 | `IKITTMAKKVG` | SEED-007 | 0.806 | 0.647 | 0.353 | REF-PIS-001 (piscidin) | ✓ NOVEL |
| 9 | SEED-006_VAR_059 | `INWKPIAAMAKKLV` | SEED-006 | 0.821 | 0.643 | 0.357 | REF-RRW-001 (tachyplesin_like) | ✓ NOVEL |
| 10 | SEED-006_VAR_071 | `IQWKGIAAMAKRLL` | SEED-006 | 0.828 | 0.643 | 0.357 | REF-SCO-001 (scorpion_isct) | ✓ NOVEL |
| 11 | SEED-006_VAR_062 | `INWRGIAAMAKKFL` | SEED-006 | 0.841 | 0.643 | 0.357 | REF-LL37-002 (cathelicidin_ll37_fragment) | ✓ NOVEL |
| 12 | SEED-006_VAR_006 | `INFKGIALMAKKLL` | SEED-006 | 0.812 | 0.643 | 0.357 | REF-FKK-001 (klaklak_analog) | ✓ NOVEL |
| 13 | SEED-008_VAR_032 | `FPVTWRFWRWWKG` | SEED-008 | 0.857 | 0.692 | 0.308 | REF-RRW-001 (tachyplesin_like) | ✓ NOVEL |
| 14 | SEED-008_VAR_009 | `FPITWRWFKWWKG` | SEED-008 | 0.849 | 0.692 | 0.308 | REF-RRW-001 (tachyplesin_like) | ✓ NOVEL |
| 15 | SEED-008_VAR_019 | `FPVSWRWWKFWKG` | SEED-008 | 0.845 | 0.692 | 0.308 | REF-IND-001 (indolicidin) | ✓ NOVEL |
| 16 | SEED-003_VAR_017 | `RRWNWRMKKMG` | SEED-003 | 0.816 | 0.182 | 0.818 | REF-RRW-001 (tachyplesin_like) | ⚠ KNOWN |
| 17 | SEED-003_VAR_012 | `RKWQYRMKKLG` | SEED-003 | 0.807 | 0.182 | 0.818 | REF-RRW-001 (tachyplesin_like) | ⚠ KNOWN |
| 18 | SEED-008_VAR_044 | `FPVTWRWWKWYRG` | SEED-008 | 0.832 | 0.600 | 0.400 | REF-IND-002 (indolicidin_analog) | ✓ NOVEL |
| 19 | SEED-005_VAR_019 | `KRLFKKAGSALKFL` | SEED-005 | 0.808 | 0.400 | 0.600 | REF-KWK-001 (template_seed_1) | ≈ CLOSE |
| 20 | SEED-001_VAR_064 | `KWKLFRKIGAVLRVL` | SEED-001 | 0.802 | 0.133 | 0.867 | REF-KWK-001 (template_seed_1) | ⚠ KNOWN |

## Interpretation

### KNOWN_VARIANT candidates

**SEED-003_VAR_017** (`RRWNWRMKKMG`) — 81.8% similar to REF-RRW-001 (tachyplesin_like; Tam_2002_J_Biol_Chem).  
The published AMP provides strong activity precedent for this candidate.
Wet-lab value: confirms assay platform works; novelty claim limited.

**SEED-003_VAR_012** (`RKWQYRMKKLG`) — 81.8% similar to REF-RRW-001 (tachyplesin_like; Tam_2002_J_Biol_Chem).  
The published AMP provides strong activity precedent for this candidate.
Wet-lab value: confirms assay platform works; novelty claim limited.

**SEED-001_VAR_064** (`KWKLFRKIGAVLRVL`) — 86.7% similar to REF-KWK-001 (template_seed_1; Oren_1997_Biochemistry).  
The published AMP provides strong activity precedent for this candidate.
Wet-lab value: confirms assay platform works; novelty claim limited.

### CLOSE_RELATIVE candidates

**SEED-005_VAR_019** (`KRLFKKAGSALKFL`) — 60.0% similar to REF-KWK-001 (template_seed_1).  
Related to a known AMP but with meaningful sequence differences. Activity probability elevated; novelty moderate.

### NOVEL candidates

16 candidates have <50% similarity to any sequence in the 72-sequence reference database.  
These represent the most scientifically novel fraction of the panel.
Discovery of activity in this subset would be publishable as a novel AMP class.

## Recommendations

1. **KNOWN_VARIANT candidates** should be de-emphasised in novelty claims but retained as positive controls that validate the assay platform.
2. **NOVEL candidates** (from seeds: SEED-006, SEED-007, SEED-008, SEED-009) are the primary discovery targets. Any confirmed activity in this subset is publishable as a novel AMP.
3. This report should be submitted with the ASSAY_PREREGISTRATION.md to document the novelty status of all candidates before wet-lab results are seen.

## Caveat

This comparison uses a curated 72-sequence reference database. A full BLASTp search against APD3 (>3,800 sequences), DRAMP v3.0 (>22,000 sequences), or dbAMP would be more comprehensive. Perform APD3 BLASTp of NOVEL candidates before publication to confirm novelty claims. See ROADMAP.md §'Beyond v1.0'.
