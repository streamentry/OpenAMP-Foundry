# Lab Partner Onboarding Guide

## Purpose

This document tells a qualified CRO or academic lab partner everything they
need to run the nominated antimicrobial peptide panel. It covers the candidate
list, synthesis instructions, assay protocols, data return format, and controls.

**This is a dry-lab nomination.** The pipeline scores are computational
predictions, not biological proof. No antimicrobial activity has been
demonstrated in vitro or in vivo.

---

## Candidate Panel

The nominated panel is **Wave 0.5**: 24 candidates across 15 scaffold families.
See `outputs/wave1_final_panel.csv` for the latest list.

### Panel composition

| Role | Count | Description |
|------|:-----:|-------------|
| BALANCED_LEAD | 15 | Predicted active + safe + novel |
| HIGH_UPSIDE_RISKY | 4 | Higher predicted activity, higher safety risk |
| POSITIVE_CONTROL | 1 | Known active AMP (magainin-1 derivative, SEED-001_VAR_064) |
| SAR_CONTROL | 4 | Known-variant sequences for SAR comparison |

### Families represented

| Family | Mechanism | Key risk |
|--------|-----------|----------|
| SEED-006 | Mastoparan-X, wasp-venom helix insertion | Mast-cell degranulation |
| SEED-007 | Bombolitin-II, bumblebee venom | Met oxidation at pos 6 |
| SEED-008 | Puroindoline-a, Trp-rich interfacial | DKP risk (F-Pro), HemoFinder HIGH |
| SEED-009 | Bac2A, proline-rich intracellular | AntiCP risk, RPMI-1640 arm recommended |
| SEED-010–019 | Wave 0.5 diversified scaffolds | See evidence certificates |

---

## Synthesis Instructions

### Peptide supplier

Any qualified SPPS provider (e.g., GenScript, LifeTein, BioMatik).

### Format

- Lyophilized powder, > 95% purity by HPLC.
- 1–2 mg per peptide (sufficient for MIC + hemolysis screening).
- Trifluoroacetate (TFA) counterion is acceptable.
- Store at −20°C, desiccated, upon receipt.

### Modifications

| Modification | Recommendation |
|-------------|---------------|
| C-terminal amidation | Recommended for all candidates (mimics natural processing) |
| N-terminal acetylation | Recommended (prevents pyroglutamate formation if N-term Q) |
| Met-containing peptides | Request norleucine (Nle) substitution to prevent oxidation |
| Cys-containing peptides | Require linear synthesis (no disulfide formation during synthesis) |

### QC requirements

- HPLC trace and MS confirmation required for each peptide.
- Purity ≥ 90% minimum; ≥ 95% preferred.
- Report observed mass vs expected mass (Da).

---

## Assay Protocols

### Primary screen: MIC (minimum inhibitory concentration)

| Parameter | Value |
|-----------|-------|
| Strains | *S. aureus* ATCC 29213, *E. coli* ATCC 25922 (minimum) |
| Method | Broth microdilution (CLSI M07) |
| Medium | Mueller-Hinton broth (MHB) |
| Concentration range | 0.5–256 µg/mL (2-fold serial dilution) |
| Incubation | 18–24 h at 37°C |
| Readout | MIC = lowest concentration with no visible growth |

Reference: CLSI M07, CLSI M100.

### Secondary screen: Hemolysis (RBC)

| Parameter | Value |
|-----------|-------|
| RBC source | Human erythrocytes (fresh, ≤ 24 h old) |
| Method | Hemoglobin release at 540 nm |
| Concentration range | Same as MIC range |
| Positive control | 1% Triton X-100 (100% hemolysis) |
| Negative control | PBS buffer (0% hemolysis) |
| Readout | HC50 = concentration causing 50% hemolysis |

Reference: Standard RBC hemolysis assay (Evans et al. 2013).

### Optional: Serum stability

| Parameter | Value |
|-----------|-------|
| Serum | 25% human serum in PBS |
| Time points | 0, 30, 60, 120, 240 min |
| Readout | RP-HPLC peak area vs t=0 |

Reference: Nguyen et al. (2010) J Biol Chem.

---

## Data Return Format

Return results as **JSON files** matching `schemas/lab_result.schema.json`.
One file per candidate per assay type.

### Required fields per file

```json
{
  "candidate_id": "SEED-007_VAR_001",
  "assay_type": "MIC",
  "organism": "Staphylococcus aureus ATCC 29213",
  "result_value": 8.0,
  "result_unit": "ug/mL",
  "positive_control_value": 2.0,
  "positive_control_unit": "ug/mL",
  "negative_control_value": null,
  "incubation_hours": 20,
  "temperature_celsius": 37,
  "medium": "MHB",
  "lab": "Partner Lab Name",
  "assay_date": "2026-08-15",
  "notes": "",
  "disclaimer": "SYNTHETIC — replace with real data"
}
```

### Files

- One JSON per candidate per assay → `SEED-007_VAR_001_MIC.json`
- Place all files in a single directory.
- See `schemas/lab_result.schema.json` for the full schema specification.

---

## Controls

### Positive control

| ID | Sequence | Expected MIC | Purpose |
|----|----------|:-----------:|---------|
| SEED-001_VAR_064 | (magainin-1 derivative) | 4–32 µg/mL | Validate assay is working |

### Negative control (if applicable)

A scrambled / inactive variant can be provided upon request to validate
specificity.

### Assay acceptance criteria

The batch is valid only if:

- Positive control MIC falls within 2-fold of expected value.
- No contamination in negative controls (sterility check).
- Hemolysis positive control (Triton X-100) produces ≥ 90% hemolysis.
- Hemolysis negative control (PBS) produces ≤ 5% hemolysis.

---

## Safety and Biosecurity

All candidates are short antimicrobial peptides (10–30 AA). They are not:

- Known toxins or virulence factors.
- Genetically modified organisms.
- Select agents (CDC/HHS list).

Standard BSL-2 practices are sufficient for MIC and hemolysis assays.
No special biocontainment is required.

---

## Timeline

| Milestone | Typical duration |
|-----------|:----------------:|
| Synthesis and QC | 2–4 weeks |
| MIC screening (2 strains × 24 candidates) | 1–2 weeks |
| Hemolysis assay (24 candidates) | 1 week |
| Data return and analysis | 1 week |

Total estimated: **5–8 weeks** from synthesis order to data return.

---

## Contact

For questions about candidate selection, protocol modifications, or data return:
open an issue at `github.com/Open-Problem-Lab/OpenAMP-Foundry` with the
`lab-partner` label.

---

## Related Documents

- `docs/WET_LAB_HANDOFF.md` — Detailed wet-lab procedure and score interpretation.
- `docs/ASSAY_PREREGISTRATION.md` — Pre-registered assay parameters.
- `docs/EXPERT_REVIEW_PACK.md` — Expert review documentation.
- `schemas/lab_result.schema.json` — Machine-readable data return schema.
- `outputs/wave1_final_panel.csv` — Current candidate list.
- `outputs/evidence_wave0_5/` — Evidence certificates for each candidate.
