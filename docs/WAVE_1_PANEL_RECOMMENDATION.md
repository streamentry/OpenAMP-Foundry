# Wave 1 Panel Recommendation

> **Disclaimer:** All scores are computational predictions.
> No antimicrobial activity has been demonstrated in vitro or in vivo.
> Wet-lab validation by qualified collaborators is required before any biological claim.
> Known/control candidates are not novelty claims.
> High-risk candidates are labeled explicitly.
> All activity and safety values are computational predictions only.

Generated: 2026-06-29
Total final panel: 24 candidates
Families represented: 15
Novel leads (HIGH_CONFIDENCE/RELATED): 9

---

## Panel Summary

| Role | Count |
|---|---|
| BALANCED_LEAD | 15 |
| HIGH_UPSIDE_RISKY | 4 |
| POSITIVE_CONTROL | 1 |
| SAR_CONTROL | 4 |

---

## Composition Answer

OpenAMP Wave 1 recommends 24 peptides across 15 independent scaffold families.

The panel includes:
- 15 balanced novel leads
- 4 high-upside / higher-risk candidates
- 5 controls (positive and SAR)

All candidates have:
- Internal OpenAMP activity and safety scores
- Novelty/prior-art classification (Levenshtein vs 72 curated references + Wave 0 panel)
- Synthesis risk flags
- Machine-readable evidence certificates (Phase 8)

External predictor review for Wave 0.5 was completed after this panel recommendation was first drafted.
Treat this file as the panel-selection record; use `docs/METRICS_CURRENT.md` for the current external-consensus state.

No antimicrobial activity is claimed until qualified wet-lab validation.

---

## Final Panel

| # | Candidate ID | Family | Sequence | Role | Activity | Safety | Novelty | Reason |
|---|---|---|---|---|---|---|---|---|
| 1 | SEED-012_VAR_005 | SEED-012 | `GKFKKLVKKLAK` | BALANCED_LEAD | 0.881 | 0.751 | CLOSE_RELATIVE | ⚠ high activity (0.881); ext safety MODERATE_RISK; novelty CLO |
| 2 | SEED-007_VAR_009 | SEED-007 | `IKFTTMLRKLG` | BALANCED_LEAD | 0.849 | 0.820 | HIGH_CONFIDENCE_NOVEL | high activity (0.849); novelty HIGH_CONFIDENCE_NOVEL; first  |
| 3 | SEED-006_VAR_062 | SEED-006 | `INWRGIAAMAKKFL` | BALANCED_LEAD | 0.841 | 0.870 | HIGH_CONFIDENCE_NOVEL | high activity (0.841); novelty HIGH_CONFIDENCE_NOVEL; first  |
| 4 | SEED-015_VAR_002 | SEED-015 | `KFLKKLFLRK` | BALANCED_LEAD | 0.836 | 1.000 | CLOSE_RELATIVE | ⚠ high activity (0.836); ext safety MODERATE_RISK; novelty CLO |
| 5 | SEED-019_VAR_006 | SEED-019 | `RVRIKFVKRALK` | BALANCED_LEAD | 0.833 | 0.934 | RELATED_NOVEL | ⚠ high activity (0.833); ext safety MODERATE_RISK; novelty REL |
| 6 | SEED-006_VAR_071 | SEED-006 | `IQWKGIAAMAKRLL` | BALANCED_LEAD | 0.828 | 0.870 | HIGH_CONFIDENCE_NOVEL | high activity (0.828); novelty HIGH_CONFIDENCE_NOVEL |
| 7 | SEED-007_VAR_001 | SEED-007 | `AKITTMLKKLG` | BALANCED_LEAD | 0.824 | 0.820 | NOVEL | high activity (0.824); novelty NOVEL |
| 8 | SEED-016_VAR_003 | SEED-016 | `RRWKIKWLKK` | BALANCED_LEAD | 0.814 | 0.940 | CLOSE_RELATIVE | ⚠ high activity (0.814); ext safety MODERATE_RISK; novelty CLO |
| 9 | SEED-019_VAR_004 | SEED-019 | `RVRIRLVKRLLK` | BALANCED_LEAD | 0.811 | 0.764 | CLOSE_RELATIVE | CLEAN LEAD pin: STRONG activity, Non-AntiCP, HemoFinder LOW; |
| 10 | SEED-016_VAR_005 | SEED-016 | `RRWKFKWLKKG` | BALANCED_LEAD | 0.810 | 1.000 | CLOSE_RELATIVE | ⚠ high activity (0.810); ext safety MODERATE_RISK; novelty CLO |
| 11 | SEED-018_VAR_004 | SEED-018 | `GKRKFILKALK` | BALANCED_LEAD | 0.773 | 1.000 | CLOSE_RELATIVE | ⚠ activity 0.773; ext safety MODERATE_RISK; novelty CLOSE_RELA |
| 12 | SEED-011_VAR_006 | SEED-011 | `FLKPVLKKLAK` | BALANCED_LEAD | 0.759 | 0.836 | CLOSE_RELATIVE | ⚠ activity 0.759; ext safety MODERATE_RISK; novelty CLOSE_RELA |
| 13 | SEED-012_VAR_002 | SEED-012 | `GKLKKLIKKLAG` | BALANCED_LEAD | 0.754 | 0.980 | CLOSE_RELATIVE | ⚠ activity 0.754; ext safety MODERATE_RISK; novelty CLOSE_RELA |
| 14 | SEED-014_VAR_006 | SEED-014 | `GKKLKILKVLGR` | BALANCED_LEAD | 0.715 | 1.000 | CLOSE_RELATIVE | ⚠ activity 0.715; ext safety MODERATE_RISK; novelty CLOSE_RELA |
| 15 | SEED-018_VAR_002 | SEED-018 | `GKRKLIFRKLK` | BALANCED_LEAD | 0.708 | 1.000 | CLOSE_RELATIVE | ⚠ activity 0.708; ext safety MODERATE_RISK; novelty CLOSE_RELA |
| 16 | SEED-008_VAR_032 | SEED-008 | `FPVTWRFWRWWKG` | HIGH_UPSIDE_RISKY | 0.857 | 0.720 | HIGH_CONFIDENCE_NOVEL | ⚠ HIGH_UPSIDE pin: activity 0.857; HIGH_CONFIDENCE_NOVEL novel |
| 17 | SEED-008_VAR_009 | SEED-008 | `FPITWRWFKWWKG` | HIGH_UPSIDE_RISKY | 0.849 | 0.720 | HIGH_CONFIDENCE_NOVEL | ⚠ HIGH_UPSIDE pin: activity 0.849; HIGH_CONFIDENCE_NOVEL novel |
| 18 | SEED-009_VAR_027 | SEED-009 | `RRLPRGPYLPKP` | HIGH_UPSIDE_RISKY | 0.808 | 0.750 | HIGH_CONFIDENCE_NOVEL | ⚠ HIGH_UPSIDE pin: activity 0.808; HIGH_CONFIDENCE_NOVEL novel |
| 19 | SEED-009_VAR_033 | SEED-009 | `RRLPRPGYMPRP` | HIGH_UPSIDE_RISKY | 0.807 | 0.750 | HIGH_CONFIDENCE_NOVEL | ⚠ HIGH_UPSIDE pin: activity 0.807; HIGH_CONFIDENCE_NOVEL novel |
| 20 | SEED-001_VAR_064 | SEED-001 | `KWKLFRKIGAVLRVL` | POSITIVE_CONTROL | 0.802 | 0.800 | KNOWN_VARIANT | Required control: POSITIVE_CONTROL |
| 21 | SEED-003_VAR_017 | SEED-003 | `RRWNWRMKKMG` | SAR_CONTROL | 0.816 | 0.800 | KNOWN_VARIANT | SAR_CONTROL anchor for tachyplesin-like class |
| 22 | SEED-005_VAR_019 | SEED-005 | `KRLFKKAGSALKFL` | SAR_CONTROL | 0.808 | 0.820 | CLOSE_RELATIVE | high activity (0.808); novelty CLOSE_RELATIVE; first candida |
| 23 | SEED-003_VAR_012 | SEED-003 | `RKWQYRMKKLG` | SAR_CONTROL | 0.807 | 0.800 | KNOWN_VARIANT | Required control: SAR_CONTROL |
| 24 | SEED-010_VAR_004 | SEED-010 | `AKRKFGWKRKFHEK` | SAR_CONTROL | 0.761 | 1.000 | KNOWN_VARIANT | ⚠ activity 0.761; ext safety LOW_EFFECTIVE (clean); novelty KN |

---

## Reserve Panel (top candidates)

| Candidate ID | Family | Sequence | Role | Exclusion Reason |
|---|---|---|---|---|
| SEED-006_VAR_059 | SEED-006 | `INWKPIAAMAKKLV` | BALANCED_LEAD | family_cap_exceeded (SEED-006 already has 2 leads) |
| SEED-006_VAR_006 | SEED-006 | `INFKGIALMAKKLL` | BALANCED_LEAD | family_cap_exceeded (SEED-006 already has 2 leads) |
| SEED-007_VAR_018 | SEED-007 | `IKISTMLKKAG` | BALANCED_LEAD | family_cap_exceeded (SEED-007 already has 2 leads) |
| SEED-007_VAR_035 | SEED-007 | `IKITTMAKKVG` | BALANCED_LEAD | family_cap_exceeded (SEED-007 already has 2 leads) |
| SEED-010_VAR_003 | SEED-010 | `AKRKHGWKRKFHEK` | SAR_CONTROL | SAR_CONTROL cap (5) reached |
| SEED-012_VAR_003 | SEED-012 | `GKLKKLIVKLLK` | BALANCED_LEAD | family_cap_exceeded (SEED-012 already has 2 leads) |
| SEED-016_VAR_006 | SEED-016 | `RRWKFKWIKR` | BALANCED_LEAD | family_cap_exceeded (SEED-016 already has 2 leads) |
| SEED-013_VAR_001 | SEED-013 | `GWGSFFKKAAHVGK` | RESERVE | EXACT_MATCH_OR_FRAGMENT — excluded as lead |
| SEED-019_VAR_005 | SEED-019 | `RVRIKLVKRLLKK` | BALANCED_LEAD | family_cap_exceeded (SEED-019 already has 2 leads) |
| SEED-006_VAR_059 | SEED-006 | `INWKPIAAMAKKLV` | BALANCED_LEAD | family_cap_exceeded (SEED-006 already has 2 leads) |
| SEED-006_VAR_006 | SEED-006 | `INFKGIALMAKKLL` | BALANCED_LEAD | family_cap_exceeded (SEED-006 already has 2 leads) |
| SEED-007_VAR_018 | SEED-007 | `IKISTMLKKAG` | BALANCED_LEAD | family_cap_exceeded (SEED-007 already has 2 leads) |

---

## Hard Rule Verification

- [x] ≥8 independent families: 15 families represented
- [x] ≤2 leads per family: verified (see family breakdown above)
- [x] ≥1 positive control: SEED-001_VAR_064 (magainin/KWKLFK-like)
- [x] Known variants labeled CONTROL/SAR_CONTROL, not LEAD
- [x] High-risk candidates labeled HIGH_UPSIDE_RISKY explicitly

---

## Family Coverage

| Family | N in Panel | Role Category |
|---|---|---|
| SEED-001 | 1 | POSITIVE_CONTROL |
| SEED-003 | 2 | SAR_CONTROL |
| SEED-005 | 1 | SAR_CONTROL |
| SEED-006 | 2 | BALANCED_LEAD |
| SEED-007 | 2 | BALANCED_LEAD |
| SEED-008 | 2 | HIGH_UPSIDE_RISKY |
| SEED-009 | 2 | HIGH_UPSIDE_RISKY |
| SEED-010 | 1 | SAR_CONTROL |
| SEED-011 | 1 | BALANCED_LEAD |
| SEED-012 | 2 | BALANCED_LEAD |
| SEED-014 | 1 | BALANCED_LEAD |
| SEED-015 | 1 | BALANCED_LEAD |
| SEED-016 | 2 | BALANCED_LEAD |
| SEED-018 | 2 | BALANCED_LEAD |
| SEED-019 | 2 | BALANCED_LEAD |

---

## Next Steps

1. Complete external predictor screen (CAMPR4, AMPScanner, Macrel, AMPActiPred, HemoFinder, AntiCP)
2. Generate evidence certificates for all final panel candidates (Phase 8)
3. Run Wave 0.5 gate checks: `make wave0-5-gate-check`
4. Expert review of HIGH_UPSIDE_RISKY candidates before synthesis
5. IP/novelty review of CLOSE_RELATIVE candidates before public disclosure
6. Submit for wet-lab synthesis — no biological claims until validated

Machine-readable data: `outputs/wave1_final_panel.csv`, `outputs/wave1_reserve_panel.csv`
