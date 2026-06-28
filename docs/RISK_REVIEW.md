# Phase 3 Risk Review

**Version:** 1.0  
**Date:** 2026-06-27  
**Reviewed by:** [Human expert sign-off required before wet-lab]

---

## Scope

This document assesses the risks associated with the Phase 3 candidate batch produced by the
OpenAMP Foundry pipeline. It covers:

1. Computational pipeline risks
2. Candidate sequence risks
3. Misuse and dual-use risks
4. Data and reproducibility risks
5. Required human review gates before proceeding

---

## 1. Computational Pipeline Risks

| Risk | Status | Mitigation |
|------|--------|-----------|
| Scoring heuristics not validated | **ACKNOWLEDGED** | All scores are labeled as computational proxies. No biological claim is made. |
| Novelty overstated | **MITIGATED** | Novelty scored by Levenshtein distance against reference seeds. Near-seeds flagged. |
| Safety score not a toxicity predictor | **ACKNOWLEDGED** | Safety score is a physicochemical heuristic only. Wet-lab hemolysis assay required. |
| Benchmark leakage | **CHECKED** | Leakage tool (`bench leakage`) run; no near-duplicates detected in candidate pool. |
| Reproducibility | **VERIFIED** | Run manifest with SHA-256 hashes of all inputs. Two runs produce identical outputs. |

---

## 2. Candidate Sequence Risks

| Risk | Status | Mitigation |
|------|--------|-----------|
| Extreme hydrophobicity (hemolysis proxy) | **FILTERED** | max_safety_risk=0.40 in phase3.yaml excludes sequences with hydrophobic_fraction > 0.65 or strong amphipathicity (μH > 0.55) |
| Extreme charge density | **FILTERED** | Poly-cationic sequences excluded by safety scorer (charge_density_ph74 > 0.55 triggers risk increment); uses pH-7.4 charge for accuracy |
| Predicted mammalian cytotoxicity | **FILTERED + DOWN-RANKED** | Selectivity proxy (charge/GRAVY ratio) flags HIGH_CYTOTOX_RISK candidates (proxy < 0.5); cytotox_penalty doubly demotes them in pilot panel selection |
| Long repeat runs (degenerate composition) | **FILTERED** | Sequences with repeat_run ≥ 6 penalised; few reach selection threshold |
| High proline content | **REPORTED** | proline_fraction > 15% incurs synthesis penalty (−0.10); flagged in expert review for pseudoproline dipeptide use; ≥25% Pro triggers `PROLINE_RICH_INTRACELLULAR` flag recommending RPMI-1640 parallel assay (Krizsan et al. 2014 Angew Chem Int Ed 53:12236) — all four SEED-009 pilot variants are flagged |
| Cysteines (disulfide bridges) | **REPORTED** | Flagged in synthesis feasibility report; reviewer must assess |
| Sequences resembling known toxins | **NOT ASSESSED** | Computational toxin screening is out of scope for this pipeline version |

**Action required:** A qualified reviewer must inspect the synthesis feasibility report
for candidates with high cysteine fraction or proline content before ordering synthesis.
Candidates with HIGH_CYTOTOX_RISK flag (selectivity_proxy < 0.5) require extra hemolysis
assay scrutiny before any mammalian cell work.

---

## 3. Misuse and Dual-Use Risks

| Risk | Status |
|------|--------|
| Pathogen enhancement | **NOT APPLICABLE** — generator produces short membrane-active peptides, not targeted virulence factors |
| Toxin design | **NOT APPLICABLE** — pipeline explicitly minimises predicted toxicity; no toxin-optimisation objective |
| Dangerous pathogen targeting | **NOT APPLICABLE** — no pathogen-specific sequences in this pipeline |
| Mass production of harmful agents | **NOT APPLICABLE** — dry-lab output only; no synthesis ordered without human review |

The generator is a conservative substitution explorer over physicochemically balanced
AMP-like templates. It does not optimise for any harmful objective.

---

## 4. Data and Reproducibility Risks

| Risk | Status | Mitigation |
|------|--------|-----------|
| Input data not versioned | **MITIGATED** | SHA-256 of all input files in `outputs/phase3_manifest.json` |
| Config changed after scoring | **MITIGATED** | Config hash in manifest; `configs/phase3.yaml` versioned in git |
| Random seed not fixed | **MITIGATED** | rng_seed=2024 hardcoded in `make generate`; documented in Makefile |
| Pipeline version not tracked | **MITIGATED** | `pipeline_version` field in manifest and evidence certificates |

---

## 5. Required Human Review Gates

The following gates must be completed by qualified humans before any candidate is
synthesised or sent to a lab partner:

| Gate | Required reviewer | Status |
|------|-------------------|--------|
| Peptide sequence review | Peptide chemist or medicinal chemist | **PENDING** |
| Target organism selection | Microbiologist | **PENDING** |
| Safety profiling plan | Safety officer or toxicologist | **PENDING** |
| Synthesis feasibility | Peptide synthesis specialist | **PENDING** |
| Batch release approval | PI or qualified scientific director | **PENDING** |
| CRO/lab partner selection | PI + legal/compliance | **PENDING** |

**No candidate may be synthesised or sent to any external party without all gates above
being cleared. This is non-negotiable.**

---

## 6. Computational Disclaimer (required)

All scores produced by the OpenAMP Foundry pipeline are transparent baseline heuristics
computed from physicochemical properties. They are NOT validated biological predictors.
No antimicrobial activity has been demonstrated in vitro or in vivo. These candidates
are nominated for possible future expert review and assay only.

Do not describe any candidate as an "antibiotic," "drug," "cure," "therapeutic," "safe,"
or "effective" without experimental evidence.

The lab is the judge.
