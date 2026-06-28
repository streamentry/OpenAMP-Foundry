"""Pre-synthesis sequence quality control for AMP candidates.

Checks each peptide sequence for synthesis difficulty, stability risks,
proteolytic vulnerabilities, and formulation concerns before ordering SPPS.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from openamp_foundry.features.physchem import aggregation_propensity as _agg_propensity
from openamp_foundry.features.physchem import net_charge_at_ph74 as _charge_at_ph74
from openamp_foundry.features.physchem import selectivity_proxy as _sel_proxy
from openamp_foundry.scoring.boman import gravy_score as _gravy


# Trypsin cleaves after K or R (except when followed by P).
_TRYPSIN_RE = re.compile(r"[KR](?!P)(?=.)")

# Chymotrypsin cleaves after F, Y, W (except when followed by P).
_CHYMOTRYPSIN_RE = re.compile(r"[FYW](?!P)(?=.)")

# Asparagine/Glutamine deamidation hotspots: N or Q followed by G or S.
# NG/NS: classic Asn deamidation via succinimide (t½ 1–30 days at pH 7.4).
# QG/QS: Gln deamidation is slower but well-documented (Geiger & Clarke 1987).
_DEAMIDATION_RE = re.compile(r"[NQ][GS]")

# Aspartate isomerization hotspots: D followed by G or S (β-Asp via succinimide).
# DG and DS motifs form β-aspartyl peptides, changing backbone geometry.
# Literature: Geiger & Clarke (1987) J Biol Chem; Tyler-Cross & Schirch (1991).
_ISOMERIZATION_RE = re.compile(r"D[GS]")

# Hydrophobic runs of ≥4 consecutive VILMFW residues → aggregation risk.
_HYDROPHOBIC_RUN_RE = re.compile(r"[VILMFW]{4,}")

# pKa values for pI calculation (simplified set).
_PKA = {
    "N_term": 8.0,
    "C_term": 3.1,
    "K": 10.5,
    "R": 12.5,
    "H": 6.0,
    "D": 3.9,
    "E": 4.1,
    "C": 8.3,
    "Y": 10.1,
}


def _net_charge_at_ph(seq: str, ph: float) -> float:
    """Approximate net charge at given pH using Henderson-Hasselbalch."""
    charge = 0.0
    # N-terminus: positive
    charge += 1.0 / (1.0 + 10 ** (ph - _PKA["N_term"]))
    # C-terminus: negative
    charge -= 1.0 / (1.0 + 10 ** (_PKA["C_term"] - ph))
    # Basic residues (positive)
    for aa, pka in [("K", _PKA["K"]), ("R", _PKA["R"]), ("H", _PKA["H"])]:
        charge += seq.count(aa) / (1.0 + 10 ** (ph - pka))
    # Acidic residues (negative)
    for aa, pka in [("D", _PKA["D"]), ("E", _PKA["E"]), ("C", _PKA["C"]), ("Y", _PKA["Y"])]:
        charge -= seq.count(aa) / (1.0 + 10 ** (pka - ph))
    return charge


def _isoelectric_point(seq: str) -> float:
    """Estimate pI by bisection on net_charge = 0."""
    lo, hi = 0.0, 14.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if _net_charge_at_ph(seq, mid) > 0:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2.0, 2)


def _molecular_weight(seq: str) -> float:
    """Approximate MW (Da) from residue masses."""
    mw = {
        "A": 89.09, "R": 174.20, "N": 132.12, "D": 133.10, "C": 121.16,
        "Q": 146.15, "E": 147.13, "G": 75.03, "H": 155.16, "I": 131.17,
        "L": 131.17, "K": 146.19, "M": 149.20, "F": 165.19, "P": 115.13,
        "S": 105.09, "T": 119.12, "W": 204.23, "Y": 181.19, "V": 117.15,
    }
    return round(sum(mw.get(aa, 110.0) for aa in seq) - 18.02 * (len(seq) - 1), 1)


def _has_uv_chromophore(seq: str) -> bool:
    return any(aa in seq for aa in "WYF")


@dataclass
class SynthQC:
    """Pre-synthesis QC result for one peptide."""

    candidate_id: str
    sequence: str
    length: int

    # Molecular properties
    molecular_weight_da: float = 0.0
    isoelectric_point: float = 0.0
    charge_ph74: float = 0.0
    charge_ph60: float = 0.0

    # Synthesis risk flags
    cysteine_count: int = 0
    methionine_count: int = 0
    has_oxidation_risk: bool = False      # C or M present
    hydrophobic_run: str = ""             # longest hydrophobic run (empty = none)
    aggregation_risk: bool = False        # run ≥ 4 hydrophobic AA (boolean gate)
    aggregation_propensity_score: float = 0.0  # continuous [0,1] from physchem.aggregation_propensity()

    # Proteolytic vulnerabilities
    trypsin_sites: list[int] = field(default_factory=list)   # positions (0-based)
    chymotrypsin_sites: list[int] = field(default_factory=list)
    deamidation_sites: list[str] = field(default_factory=list)  # e.g. ["N3G", "Q5S"]
    isomerization_sites: list[str] = field(default_factory=list)  # e.g. ["D2G", "D9S"]

    # Tryptophan photolability
    tryptophan_count: int = 0
    trp_photolability_risk: bool = False   # ≥ 3 Trp → photooxidation risk under assay lighting

    # Concentration / formulation
    has_uv_chromophore: bool = False   # W/Y/F → can use A280 for conc.
    formulation_note: str = ""

    # Hemolysis stratification (from μH)
    mu_h: float = 0.0
    hemolysis_start_conc: str = ""     # suggested starting concentration for hemolysis assay

    # Mammalian cytotoxicity risk (selectivity proxy < 0.5).
    # Default 0.0 = maximally conservative (assume cytotoxic until check_sequence() fills this).
    selectivity_proxy: float = 0.0
    cytotox_risk: bool = False

    # C-terminal modification
    c_amidation_recommended: bool = False   # request NH₂ C-terminus instead of COOH
    c_amidation_reason: str = ""

    # N-terminal acetylation
    n_acetylation_recommended: bool = False  # request Nα-Ac when interior trypsin sites exist
    n_acetylation_reason: str = ""

    # Wave 2 D-amino acid substitution guidance
    wave2_d_substitutions: list[str] = field(default_factory=list)

    # Overall flag
    flags: list[str] = field(default_factory=list)
    synthesis_difficulty: str = "LOW"   # LOW / MODERATE / HIGH

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "sequence": self.sequence,
            "length": self.length,
            "mol_weight_da": self.molecular_weight_da,
            "pI": self.isoelectric_point,
            "charge_pH7.4": round(self.charge_ph74, 2),
            "charge_pH6.0": round(self.charge_ph60, 2),
            "cysteine_count": self.cysteine_count,
            "methionine_count": self.methionine_count,
            "oxidation_risk": self.has_oxidation_risk,
            "aggregation_risk": self.aggregation_risk,
            "aggregation_propensity_score": self.aggregation_propensity_score,
            "hydrophobic_run": self.hydrophobic_run,
            "trypsin_sites": self.trypsin_sites,
            "chymotrypsin_sites": self.chymotrypsin_sites,
            "deamidation_sites": self.deamidation_sites,
            "isomerization_sites": self.isomerization_sites,
            "tryptophan_count": self.tryptophan_count,
            "trp_photolability_risk": self.trp_photolability_risk,
            "has_uv_chromophore": self.has_uv_chromophore,
            "formulation_note": self.formulation_note,
            "mu_h": self.mu_h,
            "hemolysis_start_conc": self.hemolysis_start_conc,
            "selectivity_proxy": self.selectivity_proxy,
            "cytotox_risk": self.cytotox_risk,
            "c_amidation_recommended": self.c_amidation_recommended,
            "c_amidation_reason": self.c_amidation_reason,
            "n_acetylation_recommended": self.n_acetylation_recommended,
            "n_acetylation_reason": self.n_acetylation_reason,
            "wave2_d_substitutions": self.wave2_d_substitutions,
            "flags": self.flags,
            "synthesis_difficulty": self.synthesis_difficulty,
        }


def check_sequence(candidate_id: str, seq: str, mu_h: float = 0.0) -> SynthQC:
    """Run all pre-synthesis QC checks on a single peptide sequence."""
    seq = seq.upper().strip()
    qc = SynthQC(candidate_id=candidate_id, sequence=seq, length=len(seq))

    qc.molecular_weight_da = _molecular_weight(seq)
    qc.isoelectric_point = _isoelectric_point(seq)
    qc.charge_ph74 = _net_charge_at_ph(seq, 7.4)
    qc.charge_ph60 = _net_charge_at_ph(seq, 6.0)
    qc.mu_h = mu_h

    # Oxidation-prone residues
    qc.cysteine_count = seq.count("C")
    qc.methionine_count = seq.count("M")
    qc.has_oxidation_risk = (qc.cysteine_count + qc.methionine_count) > 0

    # Aggregation / hydrophobic run
    runs = _HYDROPHOBIC_RUN_RE.findall(seq)
    if runs:
        qc.hydrophobic_run = max(runs, key=len)
        qc.aggregation_risk = True
    # Continuous aggregation score (two-component: run length + beta-branched density).
    # Provides gradient information beyond the binary aggregation_risk flag.
    qc.aggregation_propensity_score = _agg_propensity(seq)

    # Proteolytic sites (interior only — terminal K/R are typical, less risky).
    # _TRYPSIN_RE already requires a following character via (?=.), so the
    # m.start() < len(seq)-1 check is the canonical guard; the regex lookahead
    # provides a defence-in-depth backstop.
    qc.trypsin_sites = [m.start() for m in _TRYPSIN_RE.finditer(seq) if m.start() < len(seq) - 1]
    qc.chymotrypsin_sites = [m.start() for m in _CHYMOTRYPSIN_RE.finditer(seq) if m.start() < len(seq) - 1]
    # Deamidation: N/Q followed by G or S (succinimide mechanism; Geiger & Clarke 1987).
    qc.deamidation_sites = [
        f"{m.group()[0]}{m.start() + 1}{m.group()[1]}"
        for m in _DEAMIDATION_RE.finditer(seq)
    ]
    # Aspartate isomerization: D followed by G or S (β-Asp backbone rearrangement).
    qc.isomerization_sites = [
        f"{m.group()[0]}{m.start() + 1}{m.group()[1]}"
        for m in _ISOMERIZATION_RE.finditer(seq)
    ]

    # Tryptophan photolability: ≥3 Trp residues → UV-sensitive under assay lighting.
    # Trp photooxidizes to kynurenine (λmax 370 nm) and N-formylkynurenine under UV/visible
    # fluorescent light. Peptides with ≥3 Trp lose >20% activity within 4h under standard
    # lab lighting. Literature: Agon et al. (2006) Anal Biochem.
    qc.tryptophan_count = seq.count("W")
    qc.trp_photolability_risk = qc.tryptophan_count >= 3

    # UV chromophore for concentration determination
    qc.has_uv_chromophore = _has_uv_chromophore(seq)
    if qc.has_uv_chromophore:
        w_count = seq.count("W")
        y_count = seq.count("Y")
        # Simplified ε280 (M-1 cm-1): W=5500, Y=1490, disulfide bond=125 (ignored here)
        eps280 = w_count * 5500 + y_count * 1490
        if eps280 > 0:
            photo_note = (
                " KEEP AMBER VIALS OR FOIL-WRAPPED — Trp photooxidizes under lab lighting."
                if qc.trp_photolability_risk else ""
            )
            qc.formulation_note = (
                f"Use A280 for concentration (ε={eps280} M⁻¹cm⁻¹). "
                f"Dissolve in 10 mM phosphate pH 7.0; store at −80°C.{photo_note}"
            )
        else:
            qc.formulation_note = (
                "Has F — poor A280 signal; use BCA/Bradford or weight-based conc. "
                "Dissolve in 10 mM phosphate pH 7.0."
            )
    else:
        qc.formulation_note = (
            "No UV chromophore. Use BCA assay or accurate weighing (>0.1 mg) for conc. "
            "Dissolve in sterile water first; adjust to 10 mM phosphate pH 7.0."
        )

    # Hemolysis stratification by μH
    if mu_h > 0.80:
        qc.hemolysis_start_conc = f"Start at ≤MIC/10 (~{int(qc.molecular_weight_da / 100) / 10:.1f} μM range); μH={mu_h:.2f} high risk"
    elif mu_h > 0.55:
        qc.hemolysis_start_conc = f"Start at ≤MIC/3; μH={mu_h:.2f} moderate risk"
    else:
        qc.hemolysis_start_conc = f"Start at MIC; μH={mu_h:.2f} low risk"

    # Selectivity proxy (cytotoxicity risk).
    # Uses the same net_charge_at_ph74 model as compute_features() to guarantee that the
    # selectivity_proxy value here matches the one stored in the candidate feature dict
    # (side-chain only: K, R, H at pH 7.4 with pKa 6.5; D, E). The presynth_check
    # _net_charge_at_ph() model includes terminal groups/Cys/Tyr, which produces a
    # systematic offset (~0.2) and would cause divergent cytotox verdicts for the same
    # sequence when comparing feature dicts to QC reports.
    # Literature: Dathe & Wieprecht (1999) BBA; Shai (2002) BBA; Chen et al. (2005) JBC.
    qc.selectivity_proxy = _sel_proxy(_charge_at_ph74(seq), _gravy(seq))
    qc.cytotox_risk = qc.selectivity_proxy < 0.5

    # C-terminal amidation recommendation.
    # ~70% of natural helical AMPs are C-terminally amidated. Amidation:
    #   (i)  adds ~+0.5 to +1.0 net charge (replaces -COOH with -CONH₂)
    #   (ii) improves serum stability (carboxypeptidase resistance)
    #   (iii) enhances membrane binding for helical and cationic AMPs
    # Cost at synthesis: typically zero extra (specify "C-term NH₂" in order form).
    # Recommend when C-terminal residue is neutral (not K or R) AND charge < 3.0.
    c_term = seq[-1] if seq else ""
    c_term_already_charged = c_term in ("K", "R")
    if not c_term_already_charged and qc.charge_ph74 < 3.0:
        qc.c_amidation_recommended = True
        qc.c_amidation_reason = (
            f"C-terminus is {c_term!r} (neutral); charge_pH7.4={qc.charge_ph74:.1f}. "
            "Amidation adds ≈+0.5–1.0 charge, improves serum stability and membrane binding. "
            "Request 'C-terminal amide (CONH₂)' in synthesis order."
        )
    elif not c_term_already_charged:
        qc.c_amidation_recommended = False
        qc.c_amidation_reason = (
            f"C-terminus is {c_term!r} (neutral) but charge_pH7.4={qc.charge_ph74:.1f} ≥ 3.0; "
            "amidation optional — consider for serum stability improvement."
        )

    # N-terminal acetylation recommendation.
    # Nα-Ac blocks aminopeptidase-mediated N-terminal degradation (exopeptidase entry
    # blocked). Recommend whenever interior trypsin sites exist — after trypsin exposure,
    # the resulting N-terminal fragments become substrates for aminopeptidases.
    # Synthesis cost: zero — specify "N-terminal acetylation (Ac-)" in synthesis order.
    # Literature: Creighton (1993); Dhankhar et al. (2023).
    if len(qc.trypsin_sites) > 0:
        qc.n_acetylation_recommended = True
        site_positions = [p + 1 for p in qc.trypsin_sites]
        qc.n_acetylation_reason = (
            f"{len(qc.trypsin_sites)} interior trypsin site(s) detected at position(s) "
            f"{site_positions}. N-terminal acetylation (Nα-Ac) blocks aminopeptidase-mediated "
            "N-terminal degradation (exopeptidase entry blocked). Specify 'N-terminal acetylation "
            "(Ac-)' in synthesis order — zero extra cost. "
            "Literature: Creighton (1993); Dhankhar et al. (2023)."
        )

    # Wave 2 D-amino acid substitution guidance.
    # For each interior trypsin cleavage site, D-Lys or D-Arg substitution blocks trypsin
    # (requires L-stereochemistry) and extends serum t½ by an estimated 3–10×.
    # Only the 3 most N-terminal sites are listed (highest-priority targets).
    # Literature: Wade et al. 1990 PNAS.
    top_sites = sorted(qc.trypsin_sites)[:3]
    qc.wave2_d_substitutions = [
        f"Position {p + 1} ({seq[p]} → D-{'Arg' if seq[p] == 'R' else 'Lys'}): "
        "eliminates trypsin cleavage site; extend serum t½ by estimated 3–10×"
        for p in top_sites
    ]

    # Collect flags
    if qc.cysteine_count > 0:
        qc.flags.append(f"CYSTEINE×{qc.cysteine_count}: disulfide/oxidation risk — store under N₂")
    if qc.methionine_count > 0:
        qc.flags.append(f"MET×{qc.methionine_count}: oxidation risk — store at −80°C, check purity pre-assay")
    if qc.aggregation_risk:
        qc.flags.append(f"HYDROPHOBIC_RUN ({qc.hydrophobic_run}): aggregation risk — check solubility at 1 mM")
    if len(qc.trypsin_sites) > 2:
        qc.flags.append(f"TRYPSIN_SITES×{len(qc.trypsin_sites)}: low serum stability expected (<2h)")
    if qc.deamidation_sites:
        qc.flags.append(f"DEAMIDATION_RISK: {', '.join(qc.deamidation_sites)} — avoid >pH 7.5 storage; use pH 5–6 lyophilization buffer")
    if qc.isomerization_sites:
        qc.flags.append(f"ISOMERIZATION_RISK: {', '.join(qc.isomerization_sites)} — Asp→β-Asp rearrangement at neutral pH; store lyophilized at −20°C")
    if qc.charge_ph74 < 2.0:
        qc.flags.append(f"LOW_CHARGE (pH7.4={qc.charge_ph74:.1f}): reduced membrane affinity")
    if qc.c_amidation_recommended:
        qc.flags.append(
            "C_AMIDATION_RECOMMENDED: specify 'CONH₂ C-terminus' at ordering "
            "(charge boost ≈+0.7, improved serum stability)"
        )
    if qc.length > 30:
        qc.flags.append(f"LONG_PEPTIDE ({qc.length}aa): SPPS yield risk; consider native chemical ligation")

    # Synthesis difficulty rating is based on synthesis-risk flags only.
    # Guidance flags (N_ACETYLATION_RECOMMENDED, WAVE2_D_AMINO) are informational and
    # carry zero synthesis cost — they are appended after the difficulty is set.
    n_flags = len(qc.flags)
    if n_flags == 0:
        qc.synthesis_difficulty = "LOW"
    elif n_flags <= 2:
        qc.synthesis_difficulty = "MODERATE"
    else:
        qc.synthesis_difficulty = "HIGH"

    # Append informational flags after difficulty is computed (zero synthesis cost).
    if qc.cytotox_risk:
        qc.flags.append(
            f"HIGH_CYTOTOX_RISK (selectivity_proxy={qc.selectivity_proxy:.2f}): "
            "charge or GRAVY outside selective window — include mammalian cell viability "
            "assay (e.g. HC50 vs RBC, MTS vs HEK293) alongside MIC; "
            "reduce initial test concentration if cytotoxicity observed "
            "(Dathe & Wieprecht 1999 BBA; Shai 2002 BBA)"
        )
    if qc.trp_photolability_risk:
        qc.flags.append(
            f"TRP_PHOTOLABILITY ({qc.tryptophan_count} Trp): store in amber vials; "
            "handle under red/dim light; assay within 2h of thaw (Agon et al. 2006)"
        )
    if qc.n_acetylation_recommended:
        qc.flags.append(
            "N_ACETYLATION_RECOMMENDED: specify 'Ac-' (N-terminal acetyl) in synthesis order "
            "(blocks aminopeptidase entry; zero cost)"
        )
    if qc.wave2_d_substitutions:
        qc.flags.append(
            f"WAVE2_D_AMINO: {len(qc.wave2_d_substitutions)} trypsin site(s) identified for "
            "D-amino acid substitution in Wave 2 (see wave2_d_substitutions)"
        )

    return qc


def check_panel(
    candidates: list[dict],
    mu_h_map: dict[str, float] | None = None,
) -> list[SynthQC]:
    """Run QC on a list of candidate dicts (must have 'candidate_id' and 'sequence')."""
    mu_h_map = mu_h_map or {}
    results = []
    for c in candidates:
        try:
            cid = c["candidate_id"]
            seq = c["sequence"]
        except KeyError as exc:
            raise KeyError(
                f"Candidate row missing required column {exc} — "
                "check that your panel CSV has 'candidate_id' and 'sequence' headers."
            ) from exc
        results.append(check_sequence(cid, seq, mu_h=mu_h_map.get(cid, 0.0)))
    return results
