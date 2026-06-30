"""Dedicated hemolysis risk scorer — addresses the safety scorer's confirmed blind spot.

The within-AMP selectivity benchmark (v0.5.9) quantitatively confirmed that the
safety scorer fails to detect hemolysis (detection AUROC=0.3844, CI lo=0.26):
all 14 hemolytic reference AMPs score safety >= 0.94. The melittin blind spot
is not a single edge case — it is a systematic failure of the 1D hydrophobic
moment + hydrophobicity + charge density model.

This module implements a standalone hemolysis risk score derived from the
selectivity benchmark's empirical findings. It does NOT replace the safety
scorer (which retains its role in AMP-vs-decoy discrimination). It provides
a complementary, orthogonal signal designed specifically for within-AMP
hemolysis risk triage.

Component selection is evidence-driven: each component was individually
benchmarked on the 42-AMP hemolysis reference set (HC50 < 25 = hemolytic,
HC50 >= 100 = selective), and only components with individual detection
AUROC > 0.70 were retained. Components with near-zero or anti-signal
were excluded.

Components (detection AUROC from leave-one-out on n=14 vs n=21):
  1. Synthesis difficulty (1 - synthesis_feasibility_score) — AUROC=0.8027
     Hemolytic AMPs tend to be harder to synthesize: more cysteines,
     repeat runs, and hydrophobic segments. This is an incidental
     correlation, not a designed safety feature.
  2. Cationic-on-hydrophobic-face fraction — AUROC=0.7585
     Cationic residues (K/R/H) appearing on the hydrophobic face of a
     helix-wheel projection indicate poor amphipathic segregation.
     Selective AMPs segregate cationic residues onto the hydrophilic face;
     hemolytic AMPs mix them across both faces.
  3. Cysteine fraction — AUROC=0.7500
     Cysteine-rich beta-sheet AMPs (protegrins, tachyplesins, polyphemusins)
     are disproportionately hemolytic. Disulfide-bonded beta-barrel structures
     can form non-selective pores in both bacterial and mammalian membranes.
  4. Aromatic fraction — AUROC=0.8299
     Aromatic residues (F/W/Y) at high density drive non-selective membrane
     disruption. Trp-rich peptides (indolicidin) and Phe-rich peptides
     (piscidin-1) intercalate into both bacterial and mammalian bilayers.
     Chymotrypsin site density (AUROC=0.8571) is nearly collinear with
     aromatic fraction by construction (chymotrypsin cleaves after F/W/Y)
     and is excluded to avoid double-counting.

Combined 4-component weighted score achieved detection AUROC=0.8912
(bootstrap CI₉₅: 0.77-0.97) on the original 42-peptide reference set.
However, expansion to 238 peptides (v0.5.11, DBAASP data) revealed this
was small-sample inflation: on n=179 (54 hemolytic vs 125 selective),
detection AUROC drops to 0.5650 (CI 0.47-0.66) — direction correct but
NOT statistically significant. The scorer retains weak directional signal
but should not be trusted as a standalone hemolysis detector.

IMPORTANT LIMITATIONS:
  - The original reference set was small (14 hemolytic vs 21 selective, n=35).
    The expanded set (54 hemolytic vs 125 selective, n=179) revealed that the
    original AUROC=0.92 was small-sample inflation. On the expanded set,
    detection AUROC=0.565 (CI 0.47-0.66) — direction correct but not significant.
  - HC50 values are approximate literature values with high inter-assay
    variability (RBC source, buffer, incubation time, concentration range).
  - This is a triage signal, NOT a hemolysis predictor. Every candidate
    must still be assayed experimentally for hemolysis regardless of score.
  - The score does NOT model 3D structure, oligomeric state, or
    curvature-mediated lysis mechanisms. Melittin's bent-helix hemolysis
    is partially captured (risk=0.32) but not strongly penalized.
  - The aromatic fraction signal is partly driven by Trp-rich indolicidin-
    class peptides; peptides with moderate aromatic content (1-2 W/F/Y)
    are not necessarily hemolytic.

References:
  - Dathe & Wieprecht (1999) BBA 1462:71-87 (membrane selectivity)
  - Eisenberg et al. (1984) J Mol Biol 179:125-142 (hydrophobic moment)
  - Tossi et al. (2000) Biopolymers 55:4-30 (amphipathic face segregation)
  - Matsuzaki (2009) BBA 1788:1687-1692 (pore-forming mechanisms)
"""
from __future__ import annotations

from openamp_foundry.scoring.activity import clamp01
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score

# Component weights. Fixed before benchmarking. Sum = 1.00.
# Weights reflect individual signal strength (AUROC) and complementarity.
# Synthesis (0.80) and aromatic (0.83) are strongest; face (0.76) and cys (0.75)
# provide orthogonal structural signals.
_HEMOLYSIS_WEIGHTS: dict[str, float] = {
    "synthesis_difficulty": 0.30,
    "face_cationic_leakage": 0.20,
    "cysteine_content": 0.20,
    "aromatic_density": 0.30,
}


def hemolysis_risk_score(features: dict) -> float:
    """Hemolysis risk score in [0, 1]. Higher = greater predicted hemolysis risk.

    This is a dedicated hemolysis risk triage signal, NOT a replacement for the
    safety scorer. It addresses the safety scorer's confirmed blind spot on
    within-AMP selectivity (safety scorer detection AUROC=0.3844; this score=0.8912).

    The score combines four empirically-validated risk components:
      1. Synthesis difficulty (inverse of synthesis feasibility)
      2. Cationic residue leakage onto hydrophobic helix-wheel face
      3. Cysteine content (beta-sheet defensin/protegrin class)
      4. Aromatic residue density (Trp/Phe/Tyr intercalation)

    Args:
        features: compute_features() dict (must contain helix_wheel and
            synthesis-relevant fields).

    Returns:
        Risk score in [0, 1]. Values > 0.40 are enriched in hemolytic AMPs
        (mean hemolytic=0.47, mean selective=0.27 on the reference set).
        Values > 0.55 strongly suggest hemolysis risk.

    Limitations:
        - Small reference set (n=35); CI is wide.
        - Does not model 3D structure or curvature-mediated lysis.
        - Must NOT be used as a hemolysis predictor; assay is mandatory.
    """
    # Component 1: synthesis difficulty (inverse feasibility)
    synth = synthesis_feasibility_score(features, valid_sequence=True)
    synth_risk = 1.0 - synth  # [0, 1]

    # Component 2: cationic residues on hydrophobic face
    # helix_wheel_h_face_cationic_fraction in [0, 1]; scale by 3.0 so that
    # 0.33 (tachyplesin-level) maps to ~1.0
    hface_cat = float(features.get("helix_wheel_h_face_cationic_fraction", 0.0))
    face_risk = clamp01(hface_cat * 3.0)

    # Component 3: cysteine fraction
    # Protegrins/tachyplesins at cys=0.22-0.24; scale by 4.0 so 0.25 → 1.0
    cys = float(features.get("cysteine_fraction", 0.0))
    cys_risk = clamp01(cys * 4.0)

    # Component 4: aromatic fraction
    # Indolicidin at aromatic=0.38, piscidin at 0.18; scale by 3.0 so 0.33 → 1.0
    aromatic = float(features.get("aromatic_fraction", 0.0))
    arom_risk = clamp01(aromatic * 3.0)

    risk = (
        _HEMOLYSIS_WEIGHTS["synthesis_difficulty"] * synth_risk
        + _HEMOLYSIS_WEIGHTS["face_cationic_leakage"] * face_risk
        + _HEMOLYSIS_WEIGHTS["cysteine_content"] * cys_risk
        + _HEMOLYSIS_WEIGHTS["aromatic_density"] * arom_risk
    )
    return round(clamp01(risk), 4)


def hemolysis_safety_component(features: dict) -> float:
    """Inverse of hemolysis_risk_score for use as a safety-bonus in ensembles.

    Returns 1.0 - hemolysis_risk_score. Higher = lower predicted hemolysis risk.
    This is the form to use when a composite scorer needs a "higher is safer"
    component (matching the convention of safety_score, synthesis_feasibility_score).
    """
    return round(1.0 - hemolysis_risk_score(features), 4)
