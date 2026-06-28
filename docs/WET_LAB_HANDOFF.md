# Wet-Lab Handoff Guide

**Version:** 0.5.x  
**Status:** Working draft for expert review before synthesis ordering.

---

## Purpose

This document translates pipeline output scores into synthesis and assay decisions for wet-lab
scientists. Every nominated candidate has a JSON evidence certificate and a pre-synthesis QC
report. This guide explains what each number means, what action it recommends, and what to do
when fewer candidates pass the filters than expected.

---

## Score Reference Table

All scores are on a **[0, 1] scale**. Higher is better (except `disagreement`, which is lower is better).

| Score key | What it measures | Low (< 0.4) | Medium (0.4–0.7) | High (> 0.7) |
|-----------|-----------------|------------|-----------------|-------------|
| `activity` | Physicochemical similarity to known AMPs (charge, hydrophobicity, amphipathicity) | Unlikely AMP-like | Possible candidate | Strong AMP signature |
| `safety` | Absence of hemolysis risk, toxic motif similarity, mammalian membrane affinity | High host-cell risk — exclude | Monitor carefully | Safe to proceed |
| `synthesis` | SPPS synthesis feasibility (length, Cys content, repeat runs) | Difficult / high failure risk | Moderate; check QC report | Straightforward synthesis |
| `novelty` | Sequence distance from known AMP references | Near-duplicate of known AMP | Moderate novelty | New structural territory |
| `ensemble` | Weighted combination of above four scores | Below priority threshold | Borderline | Priority candidate |
| `disagreement` | |activity_likeness − boman_activity| — scorer consensus | High consensus (good) | Some divergence | Low consensus — treat cautiously |
| `amphipathic_score` | Helix-wheel face segregation (hydrophobic vs cationic face contrast) — now in pilot_panel.csv | Non-helical AMP (SEED-008/009 by design) | Partial amphipathicity | Strong helical face contrast |
| `charge_ph74` | Net charge at pH 7.4 (Henderson-Hasselbalch, not a [0,1] scale) — now in pilot_panel.csv | < +2 reduced membrane affinity | +2–+4 typical AMP range | > +5 may increase selectivity risk |

**New in pilot_panel.csv:** `amphipathic_score` and `charge_ph74` columns allow within-family prioritization — among candidates from the same seed with similar ensemble scores, prefer higher `amphipathic_score` (helical AMPs) or, for SEED-009, check that `charge_ph74 ≥ +3` (important for intracellular transport efficiency).

### Recommended Action by Ensemble Score

| Ensemble range | Recommendation |
|---------------|---------------|
| ≥ 0.70 | **Synthesise** — priority candidate |
| 0.55–0.69 | **Conditional synthesis** — review QC flags first |
| 0.40–0.54 | **Expert review required** — only if budget allows |
| < 0.40 | **Do not synthesise** — fails pipeline threshold |

---

## Selection Thresholds

The pipeline uses four gates before a candidate is marked `selected: true`.

| Gate | `pipeline.yaml` | `phase3.yaml` | Why |
|------|----------------|--------------|-----|
| `min_novelty` | ≥ 0.20 | ≥ 0.05 | Near-duplicates waste budget on already-known peptides |
| `max_safety_risk` → min safety | ≤ 0.70 → safety ≥ 0.30 | ≤ 0.40 → safety ≥ 0.60 | Phase 3 is the final synthesis batch — only clean candidates |
| `max_disagreement` | ≤ 0.45 | ≤ 0.45 | When physchem and Boman scoring diverge > threshold, both models are guessing. Both configs use 0.45 (raised from 0.40 in PR #72) — Trp-rich scaffolds (SEED-008) show disagreement ~0.43 after face_segregation_bonus correctly raised their activity scores; still blocks all genuinely uncertain candidates (no non-Trp-rich sequence exceeds 0.41) |
| Sequence validity | canonical AA only | same | Non-canonical residues are disqualified |

A candidate must pass **all four gates** to be nominated. Failing any single gate → `selected: false`.

---

## Pre-Synthesis QC Report Interpretation

Run `make presynth-qc` (or `openamp-foundry presynth-qc --panel-csv <file>`) on the final panel
before ordering. The report flags:

| Flag | Risk | Action |
|------|------|--------|
| `CYSTEINE×N` | Disulfide formation, oxidation during storage | Order under inert atmosphere; store in N₂; check purity pre-assay |
| `MET×N` | Met oxidation to sulfoxide in air | Order with >95% purity; store at −80°C; re-check purity on thaw |
| `HYDROPHOBIC_RUN (XXXX)` | Aggregation; poor aqueous solubility | Test solubility at 1 mM in PBS before assay; add 0.1% DMSO if needed |
| `TRYPSIN_SITES×N` (N > 2) | Serum degradation < 2h | Use serum-free media for initial MIC; add protease inhibitors if needed |
| `WAVE2_D_AMINO` | Wave 2 D-amino acid sites identified | See `wave2_d_substitutions` field — substitute D-Lys or D-Arg at listed positions in Wave 2 synthesis to extend serum t½ by 3–10× |
| `N_ACETYLATION_RECOMMENDED` | N-terminal aminopeptidase exposure | **Request "N-terminal acetylation (Ac-)"** in synthesis order — zero cost, blocks aminopeptidase entry |
| `DEAMIDATION_RISK` | Asn/Gln (N/Q) → Asp/Glu conversion via succinimide at pH > 7.5 (NG, NS, QG, QS motifs) | Use pH 5–6 lyophilization buffer; reconstitute in pH 7.0 just before assay; avoid >24h storage at room temperature |
| `ISOMERIZATION_RISK` | Asp (D) → β-Asp backbone rearrangement (DG, DS motifs); changes peptide geometry | Store lyophilized at −20°C; verify HPLC purity after reconstitution to detect β-Asp peaks (~+14 min retention shift) |
| `TRP_PHOTOLABILITY (N Trp)` | Trp photooxidizes to kynurenine under ambient/UV light (≥3 Trp residues) | Store in amber or foil-wrapped vials; handle under red/dim light; use aliquots; complete assay within 2h of thaw. Check A280 before and after assay for degradation. |
| `LOW_CHARGE` | Reduced membrane affinity | Lower expected potency; may need higher test concentrations |
| `LONG_PEPTIDE (>30aa)` | SPPS yield risk | Expect lower crude purity; order extra crude for purification |
| `C_AMIDATION_RECOMMENDED` | C-terminal COOH reduces charge and serum stability | **Request "C-terminal amide (CONH₂)"** in synthesis order form — adds ~+0.7 charge, improves stability at zero extra cost |
| `PROLINE_RICH_INTRACELLULAR (Pro=NN%)` | Standard MHB broth underestimates potency by 4–16× for proline-rich (≥25% Pro) AMPs that use intracellular DnaK/ribosome targets (e.g. all SEED-009 variants) | **Run a parallel assay in RPMI-1640 + 10% LB (pH 7.4)** alongside the standard MHB assay. If RPMI MIC is ≥4× lower than MHB MIC, annotate as "media-dependent uptake." (Krizsan et al. 2014 Angew Chem Int Ed 53:12236) |

### Synthesis Difficulty Rating

| Rating | Meaning | Action |
|--------|---------|--------|
| LOW | ≤ 0 flags | Standard SPPS protocol; Fmoc chemistry |
| MODERATE | 1–2 flags | Standard protocol + address specific flags above |
| HIGH | ≥ 3 flags | Discuss with peptide synthesis vendor; consider Boc chemistry or ligation |

---

## Assay Recommendations

### Initial Screen (MIC Assay)

**Reference strain panel (Wave 1 minimum):**

| Organism | ATCC strain | Gram | Rationale |
|----------|-------------|------|-----------|
| *E. coli* | ATCC 25922 | − | Gram-negative standard; reference for all AMP comparisons |
| *S. aureus* | ATCC 29213 | + | Gram-positive standard; reference for all AMP comparisons |

**MDR expansion (Wave 1 recommended — adds publication significance):**

| Organism | Strain | Resistance phenotype | Why include |
|----------|--------|----------------------|-------------|
| *S. aureus* | USA300 | MRSA (methicillin-resistant) | Clinically prevalent; any hit is immediately publishable |
| *E. coli* | ST131 (ATCC BAA-2469) | MDR (CTX-M ESBL) | Most prevalent MDR Gram-negative globally |
| *K. pneumoniae* | ATCC BAA-1705 | KPC (carbapenem-resistant) | Highest-priority WHO critical pathogen |

Including MDR strains adds only ~3× material cost but increases publication impact substantially.
Any candidate with MIC ≤ 8 μg/mL against MRSA or KPC-KP qualifies as clinically significant.

- **Growth medium:** MHB (Mueller-Hinton Broth), cation-adjusted
- **Inoculum:** ~5×10⁵ CFU/mL (CLSI standard)
- **Concentration range:** 1–128 μg/mL (2-fold serial dilutions)
- **Replicates:** ≥ 3 biological replicates per candidate
- **Positive control:** Colistin (Gram-negative), Oxacillin (Gram-positive)
- **Negative control:** Solvent blank matching highest solvent concentration

### Hemolysis Assay (Safety Gate)

Run in parallel with MIC. The `hemolysis_start_conc` field in the presynth QC report gives the
recommended starting concentration based on the computed hydrophobic moment (μH):

| μH range | Starting concentration |
|---------|----------------------|
| ≤ 0.55 | Start at MIC (low risk) |
| > 0.55 and ≤ 0.80 | Start at MIC/3 (moderate risk) |
| > 0.80 | Start at MIC/10 (high risk — very cautious) |

Use human red blood cells (hRBCs) at 0.5% in PBS. Incubate 1h at 37°C. Read at A540.
Hemolysis > 10% at MIC is a fail.

---

## SEED-006 (Mastoparan-X) Special Notes

SEED-006 variants are derived from **Mastoparan-X** (INWKGIAAMAKKLL, Yoshida *et al.* 1990),
a wasp (*Vespa xanthoptera*) venom calmodulin-binding helical peptide. This is structurally
distinct from the other 6 seeds (magainin-like, cecropin-like, tachyplesin-like, Bac2A proline-rich, puroindoline Trp-rich). 

**Mechanism:** Mastoparan-X inserts into bacterial membranes via a predominantly
**hydrophobic helix insertion** mechanism rather than electrostatic carpet disruption.
It also activates G-proteins and has calmodulin-binding properties.

**Expected activity profile:**
- Gram-positive coverage likely > Gram-negative (small outer membrane)
- May show cooperative ("all-or-nothing") dose-response curves
- Hemolytic risk: moderate (assay at MIC/3 per QC guidance)

**Synthesis guidance:**
- No Cys, no Met → standard Fmoc SPPS, standard storage
- **C-terminal amidation strongly recommended**: SEED-006_VAR_xxx candidates end in LL (hydrophobic),
  neutral C-terminus. Request `CONH₂` to add +0.7 charge and improve serum stability
- SEED-006 variants have 2–3 interior Lys → serum t½ estimated ~2–4 h

**Assay interpretation:**
- If SEED-006 variants are active but SEED-003/005/007/008/009 are not: supports calmodulin-binding
  mechanism; consider calmodulin competition assay to confirm novel mechanism
- High publication value if MIC < 4 μg/mL against MRSA (see MDR panel above)

---

## SEED-001 (Magainin-1) Special Notes

SEED-001 variants are derived from **Magainin-1** (GIGKFLHSAKKFGKAFVGEIMKS, Zasloff 1987, PNAS),
a 23-AA cationic α-helical AMP from *Xenopus laevis* (African clawed frog) skin. Our variant
SEED-001_VAR_064 (KWKLFRKIGAVLRVL, 15 AA) is a truncated, charge-optimised N-terminal segment
re-entered into the synthesis pool as the 7th scaffold family in PR #72 (face_segregation_bonus).

**Mechanism:** Toroidal-pore (wormhole) mechanism — the primary mode supported by solid-state NMR:
cationic helix is electrostatically recruited to the bacterial membrane (negative surface charge),
reorients perpendicular to the bilayer, and forms transient pores in which lipid headgroups line
the channel alongside the peptide (Matsuzaki et al. 1996, Biochemistry 35:11361; Huang 2006,
Biophys J 90:L6). At high concentrations or in truncated variants, a carpet-like detergent
mechanism may also operate (Brogden 2005, Nat Rev Microbiol 3:238). The two mechanisms differ in
assay signature: toroidal pores produce graded voltage-dependent conductance; carpet mechanism
produces a threshold-like all-or-nothing lysis. Observe dose-response shape to distinguish.

**Novelty:** LOW (0.133 vs reference set). Magainin-2 is in the reference set.
SEED-001_VAR_064 is a known-family derivative, not a novel scaffold.
**Its primary value is as a positive control confirming helix-mechanism activity at 15 AA length.**

**Scorer disagreement:** SEED-001_VAR_064 has the highest disagreement score in the pilot panel:
activity_likeness = 0.8056 (physicochemical scorer), boman_activity = 0.4286 (Boman index),
disagreement = 0.377 (gate threshold 0.45). The Boman index classifies this peptide as borderline
while the physicochemical scorer classifies it as strongly active. If SEED-001_VAR_064 is inactive
in assay, this internal disagreement is the predicted explanation — report it alongside the result.

**Expected activity profile:**
- Gram-negative and Gram-positive coverage expected (toroidal-pore/carpet disruption is broad-spectrum)
- Dose-response typically sigmoidal with a clear MIC breakpoint
- Hemolytic risk: moderate-high at high concentrations; MIC/3 starting concentration (μH = 0.53)

**Synthesis guidance:**
- No Cys, no Met → standard Fmoc SPPS, standard storage conditions
- **N-terminal acetylation strongly recommended** (5 K/R sites including K1 at N-terminus;
  Ac- blocks aminopeptidase entry and improves serum stability)
- **C-terminal amidation recommended** (`CONH₂`; adds +0.7 charge, improves serum stability)
- Serum stability model score 0.49 (borderline) — see stability section below; natural magainin
  t½ ~15–30 min in serum; N-Ac/C-NH₂ modifications are known to reduce exopeptidase exposure
  and may meaningfully extend t½ (assay with and without modifications to quantify)

**Assay interpretation:**
- If SEED-001_VAR_064 is inactive at ≤ 128 µg/mL: check HPLC purity (aggregation risk at
  shorter length); retest with 0.01% BSA to prevent tube adhesion
- If SEED-001_VAR_064 is active but MIC > 8 µg/mL: expected for a 15-mer vs. native 22-mer;
  Wave 2 should test longer variants (17–20 AA) of the same sequence
- **Target MIC ≤ 10 µg/mL**: below magainin-2 reference MIC (the 23-mer benchmark); if
  achieved, the truncation to 15 AA is biologically significant and worth reporting
- If all 6 novel seeds are inactive but SEED-001 is active: confirms the pipeline scoring
  works mechanistically, even if the novel scaffolds failed — still a useful calibration outcome

---

## SEED-003 (Cationic Trp Helix) Special Notes

SEED-003 variants are derived from **RRWQWRMKKLG** (11 AA), a tachyplesin-like
Trp/Arg-rich cationic peptide (Tam et al. 2002 J Biol Chem).

**Broad novelty classification (PR #86):** SEED-003_VAR_017 (RRWNWRMKKMG) and
SEED-003_VAR_012 (RKWQYRMKKLG) are classified **KNOWN_VARIANT** — 81.8% similar to
RRWQWRMKKLG. This has two implications:

1. **Elevated P(activity):** The parent AMP RRWQWRMKKLG is a known-active antimicrobial
   peptide. P(MIC ≤ 16 µg/mL) for SEED-003 variants is estimated 60–75% (higher than the
   general 40–55% base rate for computationally nominated AMPs).

2. **Limited novelty for publication:** Confirming activity in SEED-003 variants would
   validate the assay platform and pipeline calibration, but would not constitute a novel AMP
   discovery for publication purposes. Primary wet-lab value is as semi-known positive controls
   supplementing SEED-001_VAR_064 (the designated positive control).

**Mechanism:** Short Arg/Trp-rich cationic helix; membrane disruption via Trp indole ring
stacking and cationic electrostatic recruitment. Both scorers agree (disagreement 0.23–0.26).

**Serum stability:** Model scores 0.377 (below threshold). For 11 AA sequences, model is
calibrated above this length; actual stability may be higher. Run serum stability assay and
do not exclude on model score alone.

**Synthesis guidance:**
- RRWNWRMKKMG contains Met (M) at position 10 → oxidation risk. Request oxidation-resistant
  variant or accept Nle (norleucine) substitution as synthesis equivalent.
- Standard Fmoc SPPS; no Cys.
- **C-terminal amidation recommended** (`CONH₂`).

**Assay interpretation:**
- Activity expected based on parent AMP precedent; treat as second positive control.
- If inactive: check aggregation (Trp can cause aggregation in aqueous buffers at >200 µM);
  retry with 0.01% BSA to prevent tube binding.

---

## SEED-007 (Bombolitin-II) Special Notes

SEED-007 variants are derived from **Bombolitin-II** (IKFTTMLKKLG, 11 AA), a short amphipathic
cationic peptide from *Megabombus pennsylvanicus* (eastern bumblebee) venom (Barra *et al.* 1994,
*Biochemistry* 33:10429). This is the **largest selected family** (26 variants in pool) and
contributes **4 of the top 8 pilot panel candidates** (ranks 3, 4, 5, 8), all classified NOVEL.

**Mechanism:** Short amphipathic helical insertion. Cationic face (K2, K8, K9) is electrostatically
recruited to anionic bacterial lipid headgroups; hydrophobic face (F3, T4, T5, M6, L7, L10) inserts
into the acyl chain region. Structural similarity to mastoparan suggests G-protein co-activation is
possible but less well documented for bombolitin-class peptides.

**Novelty and publication value:**
All 4 pilot candidates are NOVEL (<50% similar to the 72-AMP reference set). Confirmed activity
in any SEED-007 variant would be directly publishable. SEED-007_VAR_009 (IKFTTMLRKLG, ensemble
0.849) is the **highest-scoring SEED-007 candidate and the highest-ranked SEED-007 variant by
greedy selection (rank 3 overall)**. Note: SEED-008_VAR_032 has a marginally higher ensemble
score (0.857, rank 13) and SEED-009_VAR_027/033 are ranked 1–2; VAR_009 is the primary
breakthrough candidate within the bombolitin family.

**Expected activity profile:**
- Gram-positive coverage likely > Gram-negative (11 AA may not fully traverse outer membrane)
- Dose-response: graded sigmoid, similar to mastoparan kinetics
- Hemolytic risk: low-moderate (μH 0.430–0.516, charge +3, amphipathic_score 0.547–0.785 —
  lower hemolysis risk than SEED-006 at comparable helix quality); mandatory HC₅₀ assay at MIC/3

**Serum stability:** Model scores 0.636–0.662 — among the **best serum stability of all NOVEL pilot
candidates** (tied with SEED-006 at 0.612–0.674; both families exceed SEED-003/005/008). Trypsin-site
density 0.273 (3 interior K/R in 11 AA) is lowest of all helical seeds. No known model bias for
short bombolitin-class peptides; scores are likely accurate. Assay to confirm.

**Synthesis guidance:**
- **All 4 pilot variants contain Met (M) at position 6** → oxidation risk. Request Nle
  (norleucine) substitution at M6, or note requirement for argon atmosphere storage and 3-month
  shelf-life limit. HPLC purity check at receipt is mandatory for Met-containing peptides.
- No Cys → standard Fmoc SPPS, no disulfide handling required.
- **C-terminal amidation recommended** (`CONH₂`) — all variants end in G (Gly); amidation adds
  +0.7 charge and reduces C-terminal exopeptidase exposure.

**Assay interpretation:**
- If SEED-007_VAR_009 (rank 3) is active but lower-ranked SEED-007 variants are not: confirms
  ensemble score correlates with MIC; focus Wave 2 on the VAR_009 scaffold.
- If all SEED-007 are inactive but SEED-006 (mastoparan) variants are active: supports GPCR /
  calmodulin-binding as the operative mechanism; review structural differences.
- If active: compare MIC vs parent Bombolitin-II (IKFTTMLKKLG) — any improvement (lower MIC
  per unit charge) from single substitutions is the primary SAR finding for publication.
- Met oxidation artefact: if inactive, request HPLC purity certificate; oxidised Met (Met→Met-sulfoxide)
  causes hydrophobic collapse and loss of amphipathicity.

---

## SEED-005 (Cecropin-Magainin Hybrid) Special Notes

SEED-005 is derived from **KRLFKKIGSALKFL** (14 AA), a synthetic cecropin-magainin hybrid
inspired by dual-domain AMP engineering (Boman *et al.* 1989; Maloy & Kari 1995, *Biopolymers*
37:105). N-terminal cecropin-like helix (KRLFKK) recruits the peptide electrostatically; C-terminal
magainin-like helix (IGSALKFL) drives hydrophobic insertion.

**Novelty classification:** CLOSE_RELATIVE — 60% similar to a reference in the 72-AMP database.
Confirmed activity would have moderate publication value (improvement over the reference AMP
is the publication angle); it does not constitute a novel scaffold discovery.

**Safety concern:** SEED-005_VAR_019 has the **lowest safety score in the pilot panel** (0.845 —
above the 0.75 gate but with less margin than all other candidates). Hemolysis assay at MIC/3 is
mandatory. If HC₅₀ < 10× MIC, deprioritise for Wave 2.

**Expected activity profile:**
- Gram-positive and Gram-negative coverage expected (cecropin N-terminal helix disrupts Gram-negative
  outer membrane; magainin-like C-terminal helix disrupts inner membrane — dual-target mechanism)
- Dose-response: sigmoidal; two-step membrane disruption may show kinetic inflection
- Hemolytic risk: moderate (safety score 0.845 — the lowest in the pilot panel; assay HC₅₀ at MIC/3)

**Serum stability:** Model score 0.449 — borderline. Second- or third-highest serum stability risk
by raw model score (comparable to SEED-008 at 0.43–0.47 with Trp steric correction), and in the
same risk tier as SEED-003. Prioritise in early serum screen. D-Lys Wave 2 substitution plan
available if t½ < 1 h.

**Synthesis guidance:**
- No Met, no Cys → standard Fmoc SPPS; no special handling.
- **C-terminal amidation recommended** (ends in L; adds +0.7 charge, improves serum stability).

**Assay interpretation:**
- Only 1 candidate in pilot panel (rank 19) — **lowest-priority family**. If resource constraints
  arise, defer to later in the assay sequence and focus resources on SEED-007/006/008/009 first.
- If active at MIC ≤ 8 µg/mL: characterise helix by circular dichroism to confirm dual-domain
  mechanism; compare MIC to parent reference AMP.

---

## SEED-008 (Puroindoline-a, Trp-rich) Special Notes

SEED-008 variants are derived from **FPVTWRWWRWWKG** (13 AA), a Trp-rich puroindoline-a fragment
from wheat (*Triticum aestivum*) grain (Dubreil *et al.* 1998, *FEBS Lett* 427:197; Clifton *et al.*
2011, *Biophys J* 100:1510). Puroindoline-a inserts into membranes via **aromatic ring stacking at
the lipid-water interface** (indole π-electron interactions with phospholipid headgroups), not via
amphipathic helix insertion.

**Novelty:** All 4 pilot candidates NOVEL. SEED-008_VAR_032 (FPVTWRFWRWWKG) has the **highest
ensemble score in the entire pilot panel** (0.857, rank 13). Publication value: high if the
non-classical mechanism is confirmed.

**Scorer note — high disagreement (0.41–0.44):** The Boman index penalises Trp as generic
hydrophobic; the activity scorer rewards it (1.5× Trp aromatic bonus). For Trp-rich AMPs acting
via indole ring insertion, **activity_likeness is the mechanistically appropriate scorer**. Do not
deprioritise SEED-008 based on Boman scores alone.

**Helix-wheel interpretation:** Amphipathic_score ≈ 0.00 and LOW_CONTRAST flag are **expected and
correct** for this non-helical AMP class. See the Helix-Wheel Amphipathic Face Analysis section.

**Expected activity profile:**
- Gram-positive coverage expected (indole affinity for phosphatidylglycerol-rich membranes);
  Gram-negative possible at higher concentrations.
- Hemolytic risk: moderate (Trp-rich sequences can be cytotoxic; HC₅₀ assay mandatory at MIC/3).

**Serum stability:** Model scores 0.43–0.47. Expected **better than model** — Trp-flanked cleavage
sites are cut 3–8× slower (Wu & Ding 2016, *J Pept Sci*). Assay before committing to D-Trp Wave 2.

**Synthesis guidance:**
- No Met, no Cys → standard Fmoc SPPS; no special modifications.
- High Trp content (3–4 Trp/13 AA): dissolve in DMSO (≤ 10% final), then dilute to assay
  concentration. Use 0.01% BSA to prevent Trp-driven tube adhesion.

**Assay interpretation:**
- If active without helical CD signal: **confirms aromatic-anchoring mechanism** — the non-helical
  CD spectrum is the novel finding; include it in the paper.
- If inactive: check aggregation first (HPLC purity in assay buffer, 0.01% BSA retry) before
  concluding negative.

---

## SEED-009 (Bac2A Proline-rich) Special Notes

SEED-009 variants are derived from **RRLPRPPRYLPRP** (13 AA), a proline-rich fragment from bovine
**Bac7/Bac2A** (*Bos taurus*; Romano *et al.* 2006, *J Pept Sci* 12:707). Proline-rich AMPs target
**intracellular pathways** — ribosome exit-tunnel stalling and DnaK chaperone inhibition — rather
than membrane disruption (Otvos *et al.* 2002, *Cell Mol Life Sci* 59:1826).

**Novelty:** All 4 pilot candidates NOVEL. Confirmed Gram-negative activity via intracellular
targeting is a high-value result; this mechanism class is under-represented in published AMPs.

**CRITICAL ASSAY REQUIREMENT — RPMI-1640 parallel assay:**
All 4 SEED-009 pilot variants carry the `PROLINE_RICH_INTRACELLULAR` presynth QC flag (Pro ≥ 25%).
Standard Mueller-Hinton broth (MHB) **underestimates potency 4–16×** because active uptake into
Gram-negative cells requires the amino acid and vitamin content of nutrient-rich media. **Run
SEED-009 variants in parallel in RPMI-1640 supplemented with 10% LB (pH 7.4)** alongside MHB.
If RPMI MIC ≤ MHB MIC / 4, annotate as "media-dependent uptake mechanism confirmed" (Krizsan
*et al.* 2014, *Angew Chem Int Ed* 53:12236).

**Serum stability:** Model scores 0.57 — mid-range by raw model score (SEED-006 0.61–0.67 and
SEED-007 0.636–0.662 are higher); expected to be **significantly better than the model score**
in practice due to Pro-bond protease resistance. Pro-X and X-Pro bonds resist all major serine proteases due to
Pro ring conformational constraint (Vanhoof *et al.* 1995, *FASEB J* 9:736–744). Bac2A-type
Pro-rich AMPs show > 2 h stability in 50% human serum (Otvos & Cudic 2002, *Curr Pharm Design*).

**Synthesis guidance:**
- No Met, no Cys → standard Fmoc SPPS.
- Pro-rich sequences (50% Pro in some variants): use extended coupling times or double-coupling
  at Pro positions; pseudoproline (Ψ-Pro) dipeptides at Pro-Ser/Thr junctions if yield is low.
- C-terminal amidation optional (Pro-rich AMPs rely less on C-terminal charge).

**Assay interpretation:**
- Expected: MHB MIC > 64 µg/mL, RPMI MIC ≤ 16 µg/mL — report both values.
- If RPMI also inactive: check charge_ph74 (must be ≥ +3 for efficient intracellular transport);
  deprioritise variants with charge_ph74 < +3 in Wave 2 design.
- Expected Gram-negative selectivity (Bac2A uptake via SbmA permease; MRSA likely resistant).
  MRSA resistance + *E. coli* / *K. pneumoniae* sensitivity is a publishable mechanistic finding.

---

## Serum Stability Model Limitations (All 7 Seeds)

The `serum_stability_score()` function is calibrated for medium-length cationic helices (~18–30 AA).
All 7 pilot panel seed families have model scores below the 0.70 threshold (t½ > 2h gate).
Complete per-family analysis:

| Scaffold | Pilot score | Issue | Expected actual t½ | Action |
|----------|-------------|-------|-------------------|--------|
| SEED-003 (cationic helix, 11–14 AA) | 0.35–0.38 | Short peptide: the trypsin-site density model was calibrated on 18–30 AA sequences. For <15 AA peptides, per-site cleavage probability and flanking-context effects dominate over the aggregate density metric; model scores below 0.40 are unreliable at this length | **Likely > model prediction** (known calibration range limitation — not a specific literature citation) | Do not exclude on serum score alone. Run assay and compare to model |
| SEED-008 (puroindoline-a, Trp-rich) | 0.43–0.47 | Indole ring bulk reduces chymotrypsin cleavage at Trp4 (steric interference) | **Likely > model prediction** — Wu & Ding (2016, J Pept Sci): Trp-flanked cleavage sites are cut 3–8× slower than Tyr/Phe equivalents | D-Trp Wave 2 plan stands; assay actual stability first — may not need D-modification |
| SEED-005 (cecropin-magainin hybrid, 14 AA) | 0.449 | Borderline score below 0.50 (t½ > 1h) threshold; only 1 pilot slot — any failure drops this family | ~30 min–1 h by model; no documented correction factor | Prioritise in early serum screen; D-Lys Wave 2 plan ready if needed |
| SEED-001 (magainin-1 derivative, 15 AA) | 0.49 | 5 K/R sites in 15-mer; natural magainin-2 has documented serum t½ 15–30 min (Park & Hahm 2005, Curr Protein Pept Sci) — score may be accurate, not a model underestimate | ~30–60 min estimated | N-terminal acetylation (recommended in QC) partially protects K1; run early serum screen before committing MIC budget; D-Lys at K3/K7 in Wave 2 if t½ < 30 min |
| SEED-009 (Bac2A proline-rich, 12 AA) | 0.57 | Pro residues confer resistance to trypsin, chymotrypsin, and elastase: Pro-X bonds cannot be hydrolysed (Pro nitrogen lacks a free H for the serine protease oxyanion hole mechanism); X-Pro bonds are very slowly cleaved due to cis-trans isomerisation barriers (Vanhoof et al. 1995, FASEB J 9:736–744). The trypsin-site density model counts K/R residues only and cannot capture this resistance. | **Likely > model prediction** — Bac2A-type Pro-rich AMPs show > 2h stability in 50% human serum (Otvos & Cudic 2002, Curr Pharm Design) | Do not penalise SEED-009 for low model score; assay confirms likely robustness |
| SEED-006 (mastoparan-X, 14 AA) | 0.61–0.67 | Near-threshold score; 2 interior Lys + moderate trypsin density; natural mastoparan t½ ~2–4 h in plasma (Rhee 1994, FEBS Lett) — score may be accurate | ~2–4 h estimated | Assay to confirm threshold passage; no special modification planned |
| SEED-007 (bombolitin-II, 11 AA) | 0.636–0.662 | Among best NOVEL-family scores (tied with SEED-006); lowest trypsin-site density of all helical seeds (3 K/R in 11 AA = 0.273 density); no known model bias for short bombolitin-class peptides | **Likely accurate** — no documented correction factor needed; assay to confirm | No modification planned; Met-containing variants require HPLC purity check at receipt |

**Recommended action before full MIC panel:**
Run a serum stability screen on all 20 pilot candidates:
- Protocol: 50% pooled human serum, 37°C, time points 0/30/60/120 min, 100 µM peptide
- Quantification: HPLC; include one stable D-peptide as positive stability control
- Cost: ~$200–400 per batch of multiple candidates (not per individual peptide)

This validates the gate assumptions directly and prevents retiring candidates that the model
incorrectly penalises.

---

## Helix-Wheel Amphipathic Face Analysis (PR #71)

The `helix_wheel_faces()` function (added in PR #71) provides a rotation-invariant analysis of
the amphipathic face architecture for each scaffold seed. Unlike the hydrophobic moment (μH),
which gives a single number, this function decomposes the helix into its hydrophobic and
hydrophilic faces and reports face contrast, cationic segregation, and amphipathic score.

**Pilot panel seed results (seeds analyzed, not all 20 variants):**

| Seed | Face Contrast | Amph Score (÷2.0) | Cationic on H-face | Mechanism | Assessment |
|------|:---:|:---:|:---:|---|---|
| SEED-003 (cationic helix, 11 AA) | 2.058 | 1.000 | 0% | Helical insertion | ✅ Ideal amphipathic architecture |
| SEED-005 (cecropin-magainin, 14 AA) | 1.942 | 0.971 | 0% | Helical insertion | ✅ Excellent amphipathic segregation |
| SEED-006 (mastoparan-X, 14 AA) | 0.960 | 0.480 | 0% | Helical insertion | ✅ Good amphipathic architecture |
| SEED-007 (bombolitin II, 11 AA) | 0.978 | 0.489 | 0% | Helical insertion | ✅ Good amphipathic architecture |
| SEED-008 (puroindoline-a, Trp-rich, 13 AA) | −0.139 | 0.000 | 8% | **Aromatic anchoring** | ⚠️ Not a classical helix-wheel AMP — expected |
| SEED-009 (Bac2A proline-rich, 12 AA) | 0.036 | 0.018 | 50% | **Intracellular (ribosome)** | ⚠️ Not a classical helix-wheel AMP — expected |

> **Note:** Amphipathic scores depend on the N-terminal convention (position-0 residue). All pipeline
> candidates are presented N→C as synthesized. Do not compare scores across circularly permuted
> representations. Magainin-2 reference: contrast=1.228, score=0.614 (with 2.0 normalization).

**Interpretation — SEED-008 and SEED-009 are non-helical AMPs (correct by design):**

The LOW_CONTRAST flags for SEED-008 and SEED-009 are NOT errors — they reflect mechanistically
distinct AMP families:

- **SEED-008 (puroindoline-a):** Trp-rich sequences insert at the membrane lipid-water interface
  via aromatic ring stacking and π-electron interactions (Trindade et al. 2014, BBA), not via
  helical amphipathic insertion. The helix wheel cannot capture this mechanism. **If SEED-008
  candidates show MIC activity despite low amphipathic_score, it confirms the non-classical
  mechanism and is a positive result.**

- **SEED-009 (Bac2A proline-rich):** Proline-rich AMPs translocate across the membrane and
  inhibit intracellular targets (ribosomes, DnaK; Otvos 2002 Cell Mol Life Sci). They have low
  face contrast and high cationic misplacement on the helical wheel by design. **MIC activity
  for SEED-009 candidates reflects intracellular targeting, not membrane disruption.**
  **CRITICAL ASSAY NOTE:** Standard Mueller-Hinton broth (MHB) underestimates proline-rich AMP
  potency by 4–16× because uptake into Gram-negative cells requires the amino acid and vitamin
  content of RPMI-1640 to drive active transport. Run SEED-009 variants **in parallel in
  RPMI-1640 supplemented with 10% LB (pH 7.4)** alongside the standard MHB assay.
  If RPMI MIC is ≥4× lower than MHB MIC, annotate as "media-dependent uptake mechanism confirmed"
  (Krizsan et al. 2014 Angew Chem Int Ed 53:12236). The presynth QC report flags this as
  `PROLINE_RICH_INTRACELLULAR` for all four SEED-009 pilot variants.

**Assay interpretation matrix:**

| SEED | MIC active + helical CD | MIC active + no helix | MIC inactive |
|------|---|---|---|
| SEED-003/005/006/007 | Confirms amphipathic insertion | Unexpected — check aggregation | Expected partial failure rate |
| SEED-008 | Unexpected — check for helix formation | Confirms aromatic insertion mechanism | Possible; try membrane disruption assay |
| SEED-009 | Not expected | Confirms intracellular mechanism | May be media-dependent — run RPMI-1640 parallel assay before concluding inactive (Krizsan 2014) |

This analysis was generated by `helix_wheel_faces()` in `features/physchem.py` and is included
in the `compute_features()` output as `helix_wheel_*` keys.

---

## Troubleshooting

### Too Few Candidates Pass the Gates

If fewer than 10 candidates are nominated from a batch:

1. Check `disagreement` scores — if many candidates cluster near the configured `max_disagreement`
   threshold (0.45 for both phase3.yaml and pipeline.yaml), the two scorers may systematically
   disagree for this peptide series. Consider whether to relax `max_disagreement` in a custom
   config (document the change and the scientific justification).
2. Check `novelty` scores — if the reference set covers your template region well, novelty will
   be low. Consider reducing `min_novelty` for that generation run only.
3. Check `safety` scores — if a hydrophobic template is used, many variants may have low safety.
   Review the safety score components (`scoring/safety.py`) for the specific risk flag.
4. Run `openamp-foundry bench leakage` to confirm candidates are not near-duplicates of each other.

### Synthesis Failure (No Product / Low Purity)

1. Check the presynth QC report for HYDROPHOBIC_RUN or LONG_PEPTIDE flags.
2. Consider pseudoproline (Ψ-Pro) dipeptides for Ser/Thr-containing sequences.
3. Consider microwave-assisted SPPS for sequences with aggregation propensity.
4. For Cys-containing peptides: use Acm protection if disulfide formation is not desired.

### All Candidates Fail Hemolysis

1. Check μH values — a high hydrophobic moment across all candidates suggests the template
   itself is hemolytic.
2. Consider substituting hydrophobic residues (L→A, F→Y) to reduce membrane disruption.
3. Re-score the modified variants through the pipeline before ordering.

---

---

## Negative Result Reporting Protocol

**All results — active and inactive — must be reported.** Selective reporting of only positive
results invalidates the pipeline's active-learning loop and creates publication bias.

### For each inactive candidate

Record the result using the schema at `schemas/lab_result.schema.json` with:

```json
{
  "result_qualitative": "inactive",
  "result_value": 128.0,
  "result_unit": "µg/mL",
  "assay_type": "MIC",
  "notes": "No growth inhibition at 128 µg/mL (top concentration tested). MIC > 128 µg/mL."
}
```

> `result_value` records the **highest concentration tested with no activity** (not `null`).
> This preserves the numerical upper bound, which is required for the active-learning loop.

### What to record for inactive candidates

| Field | Value |
|-------|-------|
| `result_qualitative` | `"inactive"` |
| `result_value` | Highest concentration tested with no activity (e.g. 128.0) |
| `result_unit` | `"µg/mL"` |
| `assay_date` | Date of the assay |
| `positive_control_passed` | Must be `true` — if false, the assay is invalid |
| `notes` | e.g. `"No activity at 128 µg/mL (top concentration). Possible hydrophobic aggregation."` |

### Diagnostic questions for inactive candidates

1. **Is μH > 0.55 and selectivity_proxy < 0.5?** → Likely hemolytic, not inactive
2. **Is synthesis_feasibility < 0.7?** → Possible synthesis failure; request HPLC purity certificate
3. **Is the seed family entirely inactive?** → Scaffold-level failure; report as family-level negative
4. **Did external predictors (CAMPR4, AMPScanner) agree it was AMP?** → Scoring model error; update reference dataset
5. **Was the peptide stored correctly?** → Check freeze-thaw cycles, solubility in MHB

### Archiving

Negative results are archived in `outputs/negative_results/` as individual JSON files named
`<candidate_id>_<assay_date>_negative.json`. The lab_result schema hash links back to the
evidence certificate that nominated the candidate. This creates a full traceability chain
for the eventual publication or open data release.

---

## Confidence Statement

All scores are **heuristic proxies** derived from physicochemical features. They have not been
calibrated against wet-lab activity data for this specific peptide series. The pipeline is a
**nomination tool**, not a predictor of MIC values. Expect a hit rate of 20–40% in initial
screens (consistent with the AMP field literature for computationally nominated candidates).

No antimicrobial activity claim is made until wet-lab confirmation.

---

## References

- CLSI M07-A10: Methods for Dilution Antimicrobial Susceptibility Tests for Bacteria That Grow Aerobically
- Boman HG (2003) Peptide antibiotics and their role in innate immunity. Annu Rev Immunol 13:61–92
- Fjell CD et al. (2011) Designing antimicrobial peptides. Nat Rev Drug Discov 11:37–51
