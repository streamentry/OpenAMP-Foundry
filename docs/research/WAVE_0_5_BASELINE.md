# Wave 0.5 Baseline — Current Panel Freeze

> **Disclaimer:** All scores are computational predictions from physicochemical heuristics.
> No antimicrobial activity has been demonstrated in vitro or in vivo.
> Wet-lab validation by qualified collaborators is required before any biological claim.
> Known/control candidates are not novelty claims.
> High-risk candidates are labeled explicitly.
> Historical note: this baseline freeze predates the completed Wave 0.5 external screen.
> Current external-predictor status now lives in `docs/evidence/METRICS_CURRENT.md` and `docs/research/ROADMAP.md`.

Generated: 2026-06-29

## Purpose

This document locks the current Wave 0 / Phase 3 candidate panel before Wave 0.5
scaffold diversification begins. It provides the reference state against which new
candidates will be compared, ensures that existing evidence is preserved exactly,
and classifies each candidate into a role that guides Wave 1 panel construction.

---

## Current Panel: 20 Candidates from 7 Seed Families

| Candidate ID | Rank | Seed | Sequence | OpenAMP Ensemble | Novelty Class | Current Role |
|---|---:|---|---|---:|---|---|
| SEED-009_VAR_033 | 1 | SEED-009 | RRLPRPGYMPRP | 0.8073 | HIGH_CONFIDENCE_NOVEL | PENDING |
| SEED-009_VAR_027 | 2 | SEED-009 | RRLPRGPYLPKP | 0.8079 | HIGH_CONFIDENCE_NOVEL | PENDING |
| SEED-007_VAR_009 | 3 | SEED-007 | IKFTTMLRKLG | 0.8493 | HIGH_CONFIDENCE_NOVEL | PENDING |
| SEED-007_VAR_001 | 4 | SEED-007 | AKITTMLKKLG | 0.8236 | NOVEL | PENDING |
| SEED-007_VAR_018 | 5 | SEED-007 | IKISTMLKKAG | 0.8145 | NOVEL | PENDING |
| SEED-009_VAR_039 | 6 | SEED-009 | RRLPRPPYIPRG | 0.7959 | HIGH_CONFIDENCE_NOVEL | PENDING |
| SEED-009_VAR_017 | 7 | SEED-009 | RRLGRPPYLGRP | 0.7985 | HIGH_CONFIDENCE_NOVEL | PENDING |
| SEED-007_VAR_035 | 8 | SEED-007 | IKITTMAKKVG | 0.8064 | NOVEL | PENDING |
| SEED-006_VAR_059 | 9 | SEED-006 | INWKPIAAMAKKLV | 0.8212 | HIGH_CONFIDENCE_NOVEL | LEAD |
| SEED-006_VAR_071 | 10 | SEED-006 | IQWKGIAAMAKRLL | 0.8275 | HIGH_CONFIDENCE_NOVEL | LEAD |
| SEED-006_VAR_062 | 11 | SEED-006 | INWRGIAAMAKKFL | 0.8405 | HIGH_CONFIDENCE_NOVEL | LEAD |
| SEED-006_VAR_006 | 12 | SEED-006 | INFKGIALMAKKLL | 0.8119 | HIGH_CONFIDENCE_NOVEL | LEAD |
| SEED-008_VAR_032 | 13 | SEED-008 | FPVTWRFWRWWKG | 0.8573 | HIGH_CONFIDENCE_NOVEL | HIGH_UPSIDE_RISKY |
| SEED-008_VAR_009 | 14 | SEED-008 | FPITWRWFKWWKG | 0.8489 | HIGH_CONFIDENCE_NOVEL | HIGH_UPSIDE_RISKY |
| SEED-008_VAR_019 | 15 | SEED-008 | FPVSWRWWKFWKG | 0.8454 | HIGH_CONFIDENCE_NOVEL | HIGH_UPSIDE_RISKY |
| SEED-003_VAR_017 | 16 | SEED-003 | RRWNWRMKKMG | 0.8161 | KNOWN_VARIANT | SAR_CONTROL |
| SEED-003_VAR_012 | 17 | SEED-003 | RKWQYRMKKLG | 0.8071 | KNOWN_VARIANT | SAR_CONTROL |
| SEED-008_VAR_044 | 18 | SEED-008 | FPVTWRWWKWYRG | 0.8322 | HIGH_CONFIDENCE_NOVEL | HIGH_UPSIDE_RISKY |
| SEED-005_VAR_019 | 19 | SEED-005 | KRLFKKAGSALKFL | 0.8081 | CLOSE_RELATIVE | LOW_PRIORITY |
| SEED-001_VAR_064 | 20 | SEED-001 | KWKLFRKIGAVLRVL | 0.802 | KNOWN_VARIANT | CONTROL |

---

## Role Definitions

| Role | Meaning |
|---|---|
| LEAD | Novel scaffold with strong activity/safety balance. Priority for synthesis. |
| HIGH_UPSIDE_RISKY | High predicted activity, but hemolysis or off-target risk flag present. |
| PENDING | Historical placeholder at the baseline-freeze date; superseded by later Wave 0.5 panel decisions. |
| CONTROL | Known AMP (KWKLFKK/magainin class). Positive control for assay calibration. |
| SAR_CONTROL | Known-variant (tachyplesin-like). SAR anchor, not a novelty lead. |
| LOW_PRIORITY | Close relative to known AMPs. Useful but weak novelty position. |

---

## Seed Family Summary

| Seed | N Candidates | Interpretation | Wave 0.5 Action |
|---|---|---|---|
| SEED-001 | 1 | Magainin/KWKLFKK analog — KNOWN_VARIANT | Retain as CONTROL |
| SEED-003 | 2 | Tachyplesin-like — KNOWN_VARIANT | Retain as SAR_CONTROL |
| SEED-005 | 1 | KWKLFKK-family close relative | CLOSE_RELATIVE, LOW_PRIORITY |
| SEED-006 | 4 | Balanced novel helices — strongest current leads | Retain all 4 as LEAD |
| SEED-007 | 4 | Temporin-G analogs — activity/safety mixed | Historical baseline note; final Wave 1 disposition is recorded elsewhere |
| SEED-008 | 4 | Trp-rich high-aromatic — high activity, HemoFinder risk | HIGH_UPSIDE_RISKY |
| SEED-009 | 4 | Pro-rich intracellular-style — AntiCP off-target risk | Historical baseline note; final Wave 1 disposition is recorded elsewhere |

---

## External Predictor Status

Historical baseline state only: at the time this file was frozen, external predictor fields had not yet been filled.
That is no longer the current repo state. The completed Wave 0.5 external screen is summarized in `docs/evidence/METRICS_CURRENT.md`, `docs/research/ROADMAP.md`, and `docs/research/WAVE_0_5_EXTERNAL_PREDICTOR_SUMMARY.md`.

The original manual-submission tool stack was:

| Tool | URL | Notes |
|---|---|---|
| CAMPR4 | http://www.camp3.bicnirrh.res.in/predict.php | Submit FASTA, record Y/N |
| AMPScanner v2 | https://www.dveltri.com/ascan/v2/ascan.html | Use threshold 0.5 |
| Macrel | https://big-data-biology.org/software/macrel | Web server; also reports hemolysis |
| AMPActiPred | (URL required) | ABP vote |
| AntiCP 2.0 | https://webs.iiitd.edu.in/raghava/anticp2/ | Off-target ACP risk, NOT AMP predictor |
| HemoFinder | (URL required) | Hemolysis risk predictor |

**AntiCP 2.0 is an off-target risk predictor, not an AMP activity predictor.**
SEED-008 is annotated HIGH hemolysis risk based on HemoFinder published data for high-Trp/Phe peptides.
SEED-009 is annotated ANTICP_RISK based on proline-rich Pro-rich class known to activate anticancer pathways.

Machine-readable status: `outputs/wave0_5_baseline.csv`

---

## Problem Statement

The current panel has 13 HIGH_CONFIDENCE_NOVEL or NOVEL candidates, but:

```
- SEED-006 (4): same scaffold family — correlated failure risk
- SEED-007 (4): same scaffold family — correlated failure risk
- SEED-008 (4): same scaffold family — correlated failure risk (hemolysis)
- SEED-009 (4): same scaffold family — correlated failure risk (off-target)
```

Only 7 seed families are represented. The panel is heavily correlated at the family level.
Wave 0.5 adds 8–12 independent new families to reduce correlated-failure risk.

---

## Preserved Data Sources

| File | SHA256 check | Contents |
|---|---|---|
| `outputs/pilot_panel.csv` | (see run_manifest.json) | 20 candidates, full scores |
| `outputs/novelty_audit_full.csv` | (see run_manifest.json) | Novelty classifications |
| `outputs/phase3_ranked.jsonl` | (see phase3_manifest.json) | Full 709-candidate scored pool |

All source files are preserved. Wave 0.5 generates **new** output files with `wave0_5_` prefix.
No existing files are modified.
