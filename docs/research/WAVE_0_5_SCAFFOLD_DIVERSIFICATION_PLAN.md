# Wave 0.5 — Scaffold Diversification Plan Summary

> **Disclaimer:** All scores are computational predictions. No antimicrobial activity has
> been demonstrated in vitro or in vivo. Wet-lab validation by qualified collaborators is
> required before any biological claim. Known/control candidates are not novelty claims.
> High-risk candidates are labeled explicitly. All activity and safety values are
> computational predictions only.

Generated: 2026-06-29

---

## Purpose

OpenAMP's Wave 0 panel (20 candidates, 7 seed families) was heavily correlated at the
family level. If one scaffold mechanism fails in wet-lab testing, multiple related variants
fail together.

Wave 0.5 adds independent scaffold families before the Wave 1 wet-lab batch to reduce
correlated-failure risk. The goal is not more candidates — it is more independent bets.

---

## What Wave 0.5 Did

| Phase | Action | Output |
|---|---|---|
| 1 — Baseline Freeze | Locked Wave 0 panel state | `docs/research/WAVE_0_5_BASELINE.md`, `outputs/wave0_5_baseline.csv` |
| 2 — Scaffold Search | Defined 10 new independent families | (design parameters in `scripts/generate_wave0_5_candidates.py`) |
| 3 — Candidate Generation | Generated 118 raw candidates | `outputs/wave0_5_raw_candidates.csv` |
| 4 — Internal Filter | Shortlisted 60 at internal gates | `outputs/wave0_5_internal_shortlist.csv` |
| 5 — External Predictors | Planned manual submissions; later completed and summarized in current-state docs | `docs/research/WAVE_0_5_EXTERNAL_PREDICTOR_SUMMARY.md`, `docs/evidence/METRICS_CURRENT.md` |
| 6 — Novelty Audit | Classified 60 shortlist vs 92 references | `outputs/wave0_5_novelty_audit.csv`, `docs/research/WAVE_0_5_NOVELTY_AUDIT.md` |
| 7 — Panel Selection | Selected 24-candidate Wave 1 panel | `outputs/wave1_final_panel.csv`, `docs/research/WAVE_1_PANEL_RECOMMENDATION.md` |
| 8 — Evidence Certificates | Generated machine-readable certs | `outputs/evidence_wave0_5/*.json` |
| 9 — Docs Update | Updated all docs | `docs/evidence/METRICS_CURRENT.md`, `docs/research/ROADMAP.md`, etc. |
| 10 — Gate Checker | Implemented W0.5-1 through W0.5-7 | `src/openamp_foundry/gates/wave0_5_gate_checker.py` |

---

## New Scaffold Families

| Family | Mechanism Class | Notes |
|---|---|---|
| SEED-010 | Histatin-5 P-113 (oral innate AMP) | Human host-defense peptide; independent from Wave 0 |
| SEED-011 | Pro-kinked helices | Disrupted amphipathicity reduces mu_h risk |
| SEED-012 | Glycine-rich low-hydrophobicity | Unique structural class; minimal hemolysis risk |
| SEED-013 | Pleurocidin/fish AMP analogs | Independent evolutionary lineage |
| SEED-014 | Scattered-helix cathelicidin-mini | Minimal cathelicidin pharmacophore |
| SEED-015 | KFLK de novo cationic | Fully designed; no natural template |
| SEED-016 | RRWK dual-Trp | Lower-aromatic Trp alternative to SEED-008 |
| SEED-017 | Pro-kinked Leu/Phe-enriched | Kinked helix with enhanced hydrophobicity |
| SEED-018 | GKRK scattered-charge | Novel charge-spacing pattern |
| SEED-019 | Arg-Val alternating | Novel beta-strand-like alternating motif |

---

## Wave 1 Final Panel

24 candidates across 13 independent scaffold families:

- 17 BALANCED_LEAD (novel, passes all internal gates)
- 4 HIGH_UPSIDE_RISKY (SEED-008 hemolysis risk, SEED-009 AntiCP risk)
- 1 POSITIVE_CONTROL (SEED-001_VAR_064)
- 2 SAR_CONTROL (SEED-003 tachyplesin-like)

---

## What Remains Pending

| Task | Status | Blocker |
|---|---|---|
| External predictor screen (all 60 shortlist) | COMPLETE | Reflected in `docs/evidence/METRICS_CURRENT.md` and `docs/research/WAVE_0_5_EXTERNAL_PREDICTOR_SUMMARY.md` |
| Wave 0.5 Gate W0.5-3 (activity consensus) | COMPLETE | Gate result recorded after external screen |
| Wave 0.5 Gate W0.5-4 (safety annotation) | COMPLETE | Gate result recorded after external screen |
| FTO (freedom-to-operate) for CLOSE_RELATIVE candidates | PENDING | Legal review |
| Expert review of HIGH_UPSIDE_RISKY candidates | PENDING | Wet-lab collaborator |

---

## Internal Gate Thresholds

All thresholds committed as source-code constants before filtering (not tuned after seeing results):

```
activity_score  >= 0.70
safety_score    >= 0.75
synthesis_score >= 0.75
novelty_proxy   >= 0.50
max_similarity_to_wave0 < 0.80
max_family_variants = 6 (shortlist cap)
max_leads_per_family = 2 (final panel cap)
```

High-upside exception (with explicit label):
```
activity_score >= 0.80 AND safety_score >= 0.65 → PASS_HIGH_UPSIDE
```

---

## Machine-Readable Index

| File | Contents |
|---|---|
| `outputs/wave0_5_baseline.csv` | 20 Wave 0 candidates with roles |
| `outputs/wave0_5_raw_candidates.csv` | 118 raw generated candidates |
| `outputs/wave0_5_internal_shortlist.csv` | 60 shortlisted candidates |
| `outputs/wave0_5_internal_excluded.csv` | 58 excluded with reasons |
| `outputs/wave0_5_external_predict_results.csv` | Optional locally generated artifact from the completed external screen; not committed in every checkout |
| `outputs/wave0_5_external_consensus.csv` | Optional locally generated artifact from the completed external screen; not committed in every checkout |
| `outputs/wave0_5_safety_consensus.csv` | Optional locally generated artifact from the completed external screen; not committed in every checkout |
| `outputs/wave0_5_novelty_audit.csv` | 60 rows with novelty classes |
| `outputs/wave1_final_panel.csv` | 24 final panel candidates |
| `outputs/wave1_reserve_panel.csv` | Reserve candidates |
| `outputs/wave0_5_panel_selection.md` | Acceptance criteria status |
| `outputs/evidence_wave0_5/*.json` | 24 machine-readable evidence certificates |
