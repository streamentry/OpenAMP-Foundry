"""Wave 0.5 raw candidate generation script.

Produces outputs/wave0_5_raw_candidates.csv with ≥80 novel-scaffold candidates
spanning 10 new seed families (SEED-010 through SEED-019).

Each family is mechanistically distinct from the current Wave 0 panel families
(SEED-001/003/005/006/007/008/009).

Required columns per the Wave 0.5 plan:
    candidate_id, seed_family, sequence, length, source_type, generation_reason,
    net_charge_pH74, hydrophobic_fraction, hydrophobic_moment, aromatic_fraction,
    boman_index, initial_activity_score, initial_safety_score, novelty_proxy,
    synthesis_flags

Novelty_proxy here is a simple heuristic: 1 - (best_similarity_to_wave0_panel).
It is NOT the full novelty audit (that is Phase 6). It gives a first-pass estimate
only. ALL values are computational — no biological activity is claimed.

Usage:
    python scripts/generate_wave0_5_candidates.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Resolve project root relative to this script
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.boman import boman_index
from openamp_foundry.scoring.safety import safety_score
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score

# ---------------------------------------------------------------------------
# Wave 0 panel sequences used for novelty_proxy (best-similarity estimate)
# ---------------------------------------------------------------------------
WAVE0_PANEL_SEQS = [
    "KWKLFRKIGAVLRVL",  # SEED-001
    "RKWQYRMKKLG",      # SEED-003
    "RRWNWRMKKMG",      # SEED-003
    "KRLFKKAGSALKFL",   # SEED-005
    "INFKGIALMAKKLL",   # SEED-006
    "INWKPIAAMAKKLV",   # SEED-006
    "INWRGIAAMAKKFL",   # SEED-006
    "IQWKGIAAMAKRLL",   # SEED-006
    "AKITTMLKKLG",      # SEED-007
    "IKFTTMLRKLG",      # SEED-007
    "IKISTMLKKAG",      # SEED-007
    "IKITTMAKKVG",      # SEED-007
    "FPITWRWFKWWKG",    # SEED-008
    "FPVSWRWWKFWKG",    # SEED-008
    "FPVTWRFWRWWKG",    # SEED-008
    "FPVTWRWWKWYRG",    # SEED-008
    "RRLGRPPYLGRP",     # SEED-009
    "RRLPRGPYLPKP",     # SEED-009
    "RRLPRPGYMPRP",     # SEED-009
    "RRLPRPPYIPRG",     # SEED-009
]

VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")


def _simple_identity(seq_a: str, seq_b: str) -> float:
    """Simple best-alignment identity (no gaps, first-aligned window)."""
    la, lb = len(seq_a), len(seq_b)
    if la == 0 or lb == 0:
        return 0.0
    shorter, longer = (seq_a, seq_b) if la <= lb else (seq_b, seq_a)
    best = 0.0
    for i in range(len(longer) - len(shorter) + 1):
        matches = sum(a == b for a, b in zip(shorter, longer[i:]))
        identity = matches / len(shorter)
        if identity > best:
            best = identity
    return round(best, 4)


def best_similarity_to_wave0(sequence: str) -> float:
    """Return maximum simple identity to any Wave 0 panel sequence."""
    return max(_simple_identity(sequence, ref) for ref in WAVE0_PANEL_SEQS)


def novelty_proxy(sequence: str) -> float:
    """1 - best_similarity. Higher = more novel relative to Wave 0 panel."""
    return round(1.0 - best_similarity_to_wave0(sequence), 4)


def synthesis_flags(sequence: str, features: dict) -> str:
    """Return comma-separated synthesis risk flags (empty string = none)."""
    flags = []
    cys_count = sequence.count("C")
    if cys_count >= 2:
        flags.append(f"CYS:{cys_count} (disulfide risk)")
    if sequence.count("P") >= 3:
        flags.append("PRO_RICH (coupling reduced)")
    if features["longest_repeat_run"] >= 4:
        flags.append(f"REPEAT_RUN:{features['longest_repeat_run']}")
    length = features["length"]
    if length > 25:
        flags.append(f"LONG:{length}AA")
    return "; ".join(flags) if flags else "NONE"


# ---------------------------------------------------------------------------
# Family definitions — 10 new seed families, SEED-010 through SEED-019
# ---------------------------------------------------------------------------
# Format: (candidate_id, sequence, source_type, generation_reason)
FAMILIES: list[tuple[str, list[tuple[str, str, str, str]]]] = [

    # SEED-010: Histatin-5 P-113 fragment analogs
    # Biological basis: P-113 (AKRHHGYKRKFHEK) is a 14-AA active fragment of
    # human salivary histatin-5. It has natural antifungal activity, low hemolysis
    # (Ruissen et al. 2001 Biochemistry), and a charge/mechanism distinct from
    # the current Wave 0 panel. Variants systematically replace the His residues
    # (partial charge at pH 7.4) with Lys/Arg or modify aromatic positions.
    # Similarity to Wave 0 panel: expected LOW (different motif class).
    ("SEED-010", [
        ("SEED-010_VAR_001", "AKRKFGYKRKFHEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; H4→K for higher cationic charge; oral innate AMP basis"),
        ("SEED-010_VAR_002", "AKRKHGYKRKFLEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; H13→L+E→K substitution; moderate charge/hydro balance"),
        ("SEED-010_VAR_003", "AKRKHGWKRKFHEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; Y8→W for increased aromatic membrane insertion"),
        ("SEED-010_VAR_004", "AKRKFGWKRKFHEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; H4→K and Y8→W; dual substitution for activity boost"),
        ("SEED-010_VAR_005", "AKRKHGYKRKFLEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; H13→L variant for balanced hydrophobicity"),
        ("SEED-010_VAR_006", "AKRKFGYKRKFLK", "DB_INSPIRED",
         "P-113 histatin5 fragment; H4→K + truncated C-term + H13→L; 13-mer"),
        ("SEED-010_VAR_007", "AKRKHGFKRKFHEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; Y8→F; reduced aromatic bulk, maintained charge"),
        ("SEED-010_VAR_008", "AKRKFGFKRKFHEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; H4→K + Y8→F; double substitution variant"),
        ("SEED-010_VAR_009", "AKRKHGYKRKLHEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; F11→L; lower hydrophobicity"),
        ("SEED-010_VAR_010", "AKRKKGWKRKFHEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; H4→K + H5→K + Y8→W; high-charge variant"),
        ("SEED-010_VAR_011", "AKRKFGYKRKFLEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; H4→K + H13→L combination"),
        ("SEED-010_VAR_012", "ARRKFGYKRKFHEK", "DB_INSPIRED",
         "P-113 histatin5 fragment; K2→R for varied charge distribution"),
    ]),

    # SEED-011: Pro-kinked short cationic helices
    # Biological basis: Proline kink disrupts the alpha-helix, creating a bent
    # peptide conformation that can penetrate membranes through a wedge mechanism
    # distinct from straight helical AMPs. Related to fragments of Magainin/MSI-78
    # analogs with engineered Pro kinks (Dathe et al. 2004 Biochemistry). The kink
    # reduces mu_h (full-sequence) while maintaining activity.
    ("SEED-011", [
        ("SEED-011_VAR_001", "FLKPILKKLAK", "DE_NOVO",
         "Pro-kinked helix; Phe-Leu N-helix + Pro kink + cationic C-helix; low full-seq mu_h"),
        ("SEED-011_VAR_002", "FLKPILKKLAKF", "DE_NOVO",
         "Pro-kinked helix; extended C-terminus Phe for membrane anchor"),
        ("SEED-011_VAR_003", "FLKPILKKLAKL", "DE_NOVO",
         "Pro-kinked helix; extended C-terminus Leu; hydrophobicity tuning"),
        ("SEED-011_VAR_004", "FLKPILRKLAK", "DE_NOVO",
         "Pro-kinked helix; K7→R substitution; Arg at bend exit improves membrane contact"),
        ("SEED-011_VAR_005", "FIKPILKKLAK", "DE_NOVO",
         "Pro-kinked helix; F1→I reduced aromatic; lower hemolysis risk"),
        ("SEED-011_VAR_006", "FLKPVLKKLAK", "DE_NOVO",
         "Pro-kinked helix; I6→V; lower hydrophobicity variant"),
        ("SEED-011_VAR_007", "FLKPILKKLKF", "DE_NOVO",
         "Pro-kinked helix; A11→K + K10→F; charge shift to C-terminus"),
        ("SEED-011_VAR_008", "FIKPILKKLKL", "DE_NOVO",
         "Pro-kinked helix; double substitution F→I + A→L; balanced safety"),
        ("SEED-011_VAR_009", "FLKPILRKLAR", "DE_NOVO",
         "Pro-kinked helix; K7→R + K10→R; higher Arg content for membrane selectivity"),
        ("SEED-011_VAR_010", "FIKPVLKKLAK", "DE_NOVO",
         "Pro-kinked helix; I→F→I + I6→V; lowest aromatic/hydro variant"),
        ("SEED-011_VAR_011", "FLKPILKKLAKR", "DE_NOVO",
         "Pro-kinked helix; C-terminal Arg addition; charge boost"),
        ("SEED-011_VAR_012", "FLKPILKKLKR", "DE_NOVO",
         "Pro-kinked helix; A11→K variant with C-terminal Arg"),
    ]),

    # SEED-012: Glycine-rich balanced cationic AMPs
    # Biological basis: Glycine-rich insect AMPs (diptericin, attacin, sarcotoxin B)
    # are a structurally distinct class with lower hemolysis than helical AMPs. The Gly
    # residues disrupt helical structure and reduce mu_h while K-rich cationic patches
    # maintain membrane activity. Here, partial Gly-substitution with K/L/V creates
    # a practical balance between activity and safety.
    ("SEED-012", [
        ("SEED-012_VAR_001", "GKLKKLVKKLLK", "DB_INSPIRED",
         "Gly-rich balanced; Gly N-cap disrupts helix start; balanced charge/hydrophobicity"),
        ("SEED-012_VAR_002", "GKLKKLIKKLAG", "DB_INSPIRED",
         "Gly-rich balanced; Gly bookend design; C-terminal Gly reduces mu_h"),
        ("SEED-012_VAR_003", "GKLKKLIVKLLK", "DB_INSPIRED",
         "Gly-rich balanced; I→V substitution; moderate hydrophobicity"),
        ("SEED-012_VAR_004", "GKLKKLVKKLAG", "DB_INSPIRED",
         "Gly-rich balanced; reduced C-terminus hydrophobicity; L11→A+L12→G"),
        ("SEED-012_VAR_005", "GKFKKLVKKLAK", "DB_INSPIRED",
         "Gly-rich balanced; L3→F aromatic substitution; aromatic membrane anchor"),
        ("SEED-012_VAR_006", "GKLKKLVKKFLK", "DB_INSPIRED",
         "Gly-rich balanced; L11→F substitution; C-terminal aromatic anchor"),
        ("SEED-012_VAR_007", "GKLRKLVKKLLK", "DB_INSPIRED",
         "Gly-rich balanced; K4→R; Arg improves lipopolysaccharide binding"),
        ("SEED-012_VAR_008", "GKLKKLVKRLLK", "DB_INSPIRED",
         "Gly-rich balanced; K8→R; Arg at C-terminal cationic patch"),
        ("SEED-012_VAR_009", "GKLKKLVKKLAK", "DB_INSPIRED",
         "Gly-rich balanced; L11→A; reduced tail hydrophobicity for safer profile"),
        ("SEED-012_VAR_010", "GKFKKLIKKLAG", "DB_INSPIRED",
         "Gly-rich balanced; dual F and I aromatic/hydrophobic substitution"),
        ("SEED-012_VAR_011", "GKLKKLVKKLVK", "DB_INSPIRED",
         "Gly-rich balanced; L11→V; Val tail for reduced hemolysis"),
        ("SEED-012_VAR_012", "GKFKRLVKKLAK", "DB_INSPIRED",
         "Gly-rich balanced; Phe aromatic + Arg substitution combination"),
    ]),

    # SEED-013: Pleurocidin/fish AMP-inspired short peptides
    # Biological basis: Pleurocidin (GWGSFFKKAAHVGKHVGKAALTHYL) is a winter flounder
    # antimicrobial peptide with broad activity and relatively low hemolysis compared
    # to melittin (Patrzykat et al. 2002 Antimicrob Agents Chemother). The N-terminal
    # active fragment contains GWGSFFKKAAHVG (13-14 AA), which is rich in Gly and Ser
    # giving low mu_h despite having Phe and Trp for membrane insertion.
    ("SEED-013", [
        ("SEED-013_VAR_001", "GWGSFFKKAAHVGK", "DB_INSPIRED",
         "Pleurocidin N-terminal fragment; Gly-Ser scaffold reduces amphipathicity; fish AMP"),
        ("SEED-013_VAR_002", "GWGSFFKKAAHVGR", "DB_INSPIRED",
         "Pleurocidin fragment; K14→R; Arg C-terminus for improved gram-negative activity"),
        ("SEED-013_VAR_003", "GWGSFFKKAAHVAK", "DB_INSPIRED",
         "Pleurocidin fragment; G13→A; increased hydrophobicity variant"),
        ("SEED-013_VAR_004", "GWGSFFKRAAHVGK", "DB_INSPIRED",
         "Pleurocidin fragment; K8→R; Arg substitution for Lys at cationic patch"),
        ("SEED-013_VAR_005", "GWGAFFKKAAHVGK", "DB_INSPIRED",
         "Pleurocidin fragment; S4→A; dehydration-stable Ala variant"),
        ("SEED-013_VAR_006", "GWGSFFKKAAYVGK", "DB_INSPIRED",
         "Pleurocidin fragment; H12→Y; aromatic modification at hydrophobic tail"),
        ("SEED-013_VAR_007", "GWGSFLKKAAHVGK", "DB_INSPIRED",
         "Pleurocidin fragment; F6→L; reduced aromatic content for lower hemolysis"),
        ("SEED-013_VAR_008", "GWGAFFKRAAHVGK", "DB_INSPIRED",
         "Pleurocidin fragment; S4→A + K8→R double substitution"),
        ("SEED-013_VAR_009", "GWGAFFKKAAHVAK", "DB_INSPIRED",
         "Pleurocidin fragment; S4→A + G13→A; increased hydrophobicity balance"),
        ("SEED-013_VAR_010", "GWGSFFKKAAYVAK", "DB_INSPIRED",
         "Pleurocidin fragment; H12→Y + G13→A combination"),
        ("SEED-013_VAR_011", "GWGSFFKKAAHVGKK", "DB_INSPIRED",
         "Pleurocidin fragment; C-terminal Lys extension for higher charge"),
        ("SEED-013_VAR_012", "GWGSFFKKAAHIGK", "DB_INSPIRED",
         "Pleurocidin fragment; V13→I; increased hydrophobicity at membrane anchor"),
    ]),

    # SEED-014: Scattered-helix cathelicidin-mini peptides
    # Biological basis: Mini-cathelicidin peptides (e.g. from BMAP-28, CRAMP fragments)
    # where Gly N-cap disrupts helix initiation and K/R residues are distributed across
    # all helix faces rather than concentrated on the polar face. This "scattered" charge
    # arrangement lowers mu_h while maintaining cationic membrane activity.
    # Distinct from SEED-007 (temporin-G analog) and SEED-006 (IAAM-core helices).
    ("SEED-014", [
        ("SEED-014_VAR_001", "GRKFKILKVLGK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; Gly N-cap + Phe aromatic + distributed K/R"),
        ("SEED-014_VAR_002", "GRKLKILKVLGK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; template with all-Leu hydrophobic residues"),
        ("SEED-014_VAR_003", "GRKLKILKVLRK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; C-terminal K→R for higher Arg content"),
        ("SEED-014_VAR_004", "GRKLRILKVLGK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; K4→R; Arg-rich N-terminal segment"),
        ("SEED-014_VAR_005", "GRKLKILKVLGKK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; C-terminal KK extension for higher charge"),
        ("SEED-014_VAR_006", "GKKLKILKVLGR", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; R→G swap + C-terminal Arg"),
        ("SEED-014_VAR_007", "GRKLKILKVIGK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; V9→I; hydrophobicity increase"),
        ("SEED-014_VAR_008", "GRKFKILKVLRK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; Phe + C-terminal Arg; higher activity"),
        ("SEED-014_VAR_009", "GRKLKLVKVLGK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; I6→L + K7→V; hydrophobicity shift"),
        ("SEED-014_VAR_010", "GRKFRLVKVLGK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; Phe + K4→R + L6→V combination"),
        ("SEED-014_VAR_011", "GRKLKILKVLAK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; G12→A; tail hydrophobicity increase"),
        ("SEED-014_VAR_012", "GRKFKILKVLAK", "DE_NOVO",
         "Scattered-charge cathelicidin-mini; Phe + G12→A combination"),
    ]),

    # SEED-015: KFLK-repeat de novo cationic peptides
    # Biological basis: Designed short cationic peptides using the Phe-Leu-Lys motif
    # at helical-wheel positions. Pattern: (K)(F)(L)(K) × n. The Phe aromatic provides
    # membrane insertion; Lys provides cationic charge; Leu contributes hydrophobicity.
    # No natural template — de novo design principle inspired by template-designed AMPs
    # (Chongsiriwatana et al. 2008 PNAS). Safety: no Cys, low Pro, moderate mu_h.
    ("SEED-015", [
        ("SEED-015_VAR_001", "KFLKKLFLKK", "DE_NOVO",
         "KFLK-repeat de novo; Phe+Leu hydrophobic face; Lys cationic; minimal hemolysis"),
        ("SEED-015_VAR_002", "KFLKKLFLRK", "DE_NOVO",
         "KFLK-repeat de novo; K10→R; terminal Arg improves LPS binding"),
        ("SEED-015_VAR_003", "KFLKKLILKK", "DE_NOVO",
         "KFLK-repeat de novo; F7→I; reduced aromatic content"),
        ("SEED-015_VAR_004", "KFLKKLFLKKA", "DE_NOVO",
         "KFLK-repeat de novo; Ala extension; charge maintained"),
        ("SEED-015_VAR_005", "KFLKKLFLKR", "DE_NOVO",
         "KFLK-repeat de novo; K10→R shorter variant; higher Arg ratio"),
        ("SEED-015_VAR_006", "RFLKKLFLKK", "DE_NOVO",
         "KFLK-repeat de novo; K1→R; N-terminal Arg for membrane selectivity"),
        ("SEED-015_VAR_007", "KFLKKLFLRKK", "DE_NOVO",
         "KFLK-repeat de novo; K9→R; 11-mer with internal Arg"),
        ("SEED-015_VAR_008", "KFLKKLILRKK", "DE_NOVO",
         "KFLK-repeat de novo; F7→I + K9→R; dual substitution safer variant"),
        ("SEED-015_VAR_009", "KFLKKLFLKKG", "DE_NOVO",
         "KFLK-repeat de novo; C-terminal Gly reduces mu_h slightly"),
        ("SEED-015_VAR_010", "KFLKKLFLKKL", "DE_NOVO",
         "KFLK-repeat de novo; Leu extension; hydrophobicity increase"),
        ("SEED-015_VAR_011", "KFLKKFILKK", "DE_NOVO",
         "KFLK-repeat de novo; L7→F; higher aromatic content variant"),
        ("SEED-015_VAR_012", "KFLKKLFLKKR", "DE_NOVO",
         "KFLK-repeat de novo; 11-mer with C-terminal Arg; charge/length extension"),
    ]),

    # SEED-016: RRWK-moderate-Trp AMPs
    # Biological basis: Short Arg-Arg-Trp peptides inspired by the cathelicidin RRWWRF
    # (Strom et al. 2003 J Pept Sci) but with lower Trp content than SEED-008 (which has
    # 3-4 Trp per 13-AA). These contain only 2 Trp residues, shifting the mechanism from
    # bulk membrane disruption (SEED-008 type) toward an Arg-mediated electrostatic + Trp
    # insertion dual mechanism. Much lower hemolysis risk than SEED-008.
    ("SEED-016", [
        ("SEED-016_VAR_001", "RRWKFKWLKK", "DE_NOVO",
         "RRWK dual-Trp; 2-Trp lower hemolysis vs SEED-008 4-Trp; Arg-Trp dual mechanism"),
        ("SEED-016_VAR_002", "RRWKFKWLKR", "DE_NOVO",
         "RRWK dual-Trp; K10→R; Arg-enriched terminal"),
        ("SEED-016_VAR_003", "RRWKIKWLKK", "DE_NOVO",
         "RRWK dual-Trp; F5→I; reduced aromatic at position 5"),
        ("SEED-016_VAR_004", "RRWKFKWIKK", "DE_NOVO",
         "RRWK dual-Trp; L8→I; lower hydrophobicity at hydrophobic face"),
        ("SEED-016_VAR_005", "RRWKFKWLKKG", "DE_NOVO",
         "RRWK dual-Trp; C-terminal Gly extension; mu_h reduction"),
        ("SEED-016_VAR_006", "RRWKFKWIKR", "DE_NOVO",
         "RRWK dual-Trp; L8→I + K10→R double substitution"),
        ("SEED-016_VAR_007", "RRWKFKWLKRK", "DE_NOVO",
         "RRWK dual-Trp; 11-mer with double C-terminal Arg-Lys"),
        ("SEED-016_VAR_008", "RRWKIKWIKK", "DE_NOVO",
         "RRWK dual-Trp; F5→I + L8→I; minimal aromatic variant"),
        ("SEED-016_VAR_009", "RRWRFKWLKK", "DE_NOVO",
         "RRWK dual-Trp; K4→R; all-Arg cationic residues"),
        ("SEED-016_VAR_010", "RRWKFKWLAK", "DE_NOVO",
         "RRWK dual-Trp; K9→A; charge reduction to test selectivity window"),
        ("SEED-016_VAR_011", "KRWKFKWLKK", "DE_NOVO",
         "RRWK dual-Trp; R1→K; Lys-first variant for synthesis simplicity"),
        ("SEED-016_VAR_012", "RRWKFKWLKKL", "DE_NOVO",
         "RRWK dual-Trp; Leu extension; 11-mer with increased hydrophobicity"),
    ]),

    # SEED-017: Pro-kinked Leu/Phe-enriched AMPs (extended SEED-011 class)
    # Biological basis: Second Pro-kink family with higher Phe and Leu content,
    # representing a different region of the Pro-kinked AMP sequence space. While
    # SEED-011 uses Ile as the primary hydrophobic residue, SEED-017 uses Phe+Leu
    # for stronger membrane insertion. The Pro kink reduces mu_h below the hemolysis
    # threshold despite high Phe content. Inspired by the membrane-disruptive fragment
    # class from Pardaxin analogs (Oren & Shai 2000).
    ("SEED-017", [
        ("SEED-017_VAR_001", "KFLPKLIIKLLK", "DE_NOVO",
         "Pro-kinked Phe-Leu; I×2 hydrophobic core; Phe N-anchor; Pro kink position 4"),
        ("SEED-017_VAR_002", "FLPILKKLARKLL", "DE_NOVO",
         "Pro-kinked Phe-Leu; brevinin-inspired; Arg at C-helix start for charge balance"),
        ("SEED-017_VAR_003", "FLPILKKLAKKLL", "DE_NOVO",
         "Pro-kinked Phe-Leu; KK cationic patch C-terminal; balanced charge/hydro"),
        ("SEED-017_VAR_004", "KFLPKLIIKKLK", "DE_NOVO",
         "Pro-kinked Phe-Leu; K11→K + KK patch; high charge density variant"),
        ("SEED-017_VAR_005", "KFLPKLILKLLK", "DE_NOVO",
         "Pro-kinked Phe-Leu; I7→L; all-Leu hydrophobic core"),
        ("SEED-017_VAR_006", "KFLPKLIIKALK", "DE_NOVO",
         "Pro-kinked Phe-Leu; L11→A; reduced tail hydrophobicity"),
        ("SEED-017_VAR_007", "KFIPKLIIKLLK", "DE_NOVO",
         "Pro-kinked Phe-Leu; L3→I; I-enriched vs Leu-enriched variant"),
        ("SEED-017_VAR_008", "KFLPKLFIKLLK", "DE_NOVO",
         "Pro-kinked Phe-Leu; I7→F; dual-Phe aromatic variant"),
        ("SEED-017_VAR_009", "KFLPRLVIKLLK", "DE_NOVO",
         "Pro-kinked Phe-Leu; K5→R; N-helix Arg for LPS interaction"),
        ("SEED-017_VAR_010", "KFLPKLIIKLAR", "DE_NOVO",
         "Pro-kinked Phe-Leu; K12→R; C-terminal Arg"),
        ("SEED-017_VAR_011", "KFLPKLIAKLLK", "DE_NOVO",
         "Pro-kinked Phe-Leu; I8→A; de-risked hydrophobicity variant"),
        ("SEED-017_VAR_012", "KFLPKLIIALLK", "DE_NOVO",
         "Pro-kinked Phe-Leu; K9→A + L10→L; charge reduction safety probe"),
    ]),

    # SEED-018: GKRK-type scattered-charge cationic AMPs
    # Biological basis: Short peptides where Gly N-cap disrupts helix formation and
    # charge residues (Lys, Arg) are scattered across positions to prevent a concentrated
    # polar helix face. This reduces mu_h while preserving electrostatic activity.
    # Hydrophobic residues limited to Leu, Ile, Phe to avoid very high hydrophobic_fraction.
    # Inspired by short BMAP-derived design principles (Turner et al. 1998 J Pept Sci).
    ("SEED-018", [
        ("SEED-018_VAR_001", "GKRKLILKALK", "DE_NOVO",
         "GKRK scattered charge; Gly-cap + Lys/Arg spread; Ala tail for low mu_h"),
        ("SEED-018_VAR_002", "GKRKLIFRKLK", "DE_NOVO",
         "GKRK scattered charge; Phe aromatic insertion residue; Arg mid-sequence"),
        ("SEED-018_VAR_003", "GKRKLILKRLK", "DE_NOVO",
         "GKRK scattered charge; K9→R; additional Arg for selectivity"),
        ("SEED-018_VAR_004", "GKRKFILKALK", "DE_NOVO",
         "GKRK scattered charge; L5→F aromatic swap; low charge density variant"),
        ("SEED-018_VAR_005", "GKRKLIFRALK", "DE_NOVO",
         "GKRK scattered charge; Phe + C-terminal Ala-Lys"),
        ("SEED-018_VAR_006", "GKRKLILKKLK", "DE_NOVO",
         "GKRK scattered charge; A10→K; higher charge density variant"),
        ("SEED-018_VAR_007", "GKRKLIVKALK", "DE_NOVO",
         "GKRK scattered charge; L7→V; Val for lower hemolysis risk"),
        ("SEED-018_VAR_008", "GKRKFILRALK", "DE_NOVO",
         "GKRK scattered charge; Phe + K8→R; aromatic + Arg combination"),
        ("SEED-018_VAR_009", "GKRKLIVKRLK", "DE_NOVO",
         "GKRK scattered charge; V7 + K9→R; low hydrophobicity + Arg"),
        ("SEED-018_VAR_010", "GKRKLILKALKK", "DE_NOVO",
         "GKRK scattered charge; C-terminal Lys extension; charge boost"),
        ("SEED-018_VAR_011", "GKRKFILKRLK", "DE_NOVO",
         "GKRK scattered charge; Phe + K8→R; aromatic and Arg combination"),
        ("SEED-018_VAR_012", "GKRKLIIKALK", "DE_NOVO",
         "GKRK scattered charge; L5→I; Ile for lower bulk hydrophobicity"),
    ]),

    # SEED-019: Arg-Val/Ile alternating AMPs
    # Biological basis: Short peptides with alternating basic (Arg) and hydrophobic
    # (Val/Ile) residues, inspired by the design principle of RV-23 and similar
    # synthetic peptides (Blondelle & Houghten 1992 Biochemistry). The alternating
    # pattern produces an irregular amphipathicity (low mu_h) while maintaining
    # cationic charge and hydrophobic content. Mechanistically distinct from all
    # current Wave 0 families: not helical, not Pro-rich, not Trp-rich.
    ("SEED-019", [
        ("SEED-019_VAR_001", "RVRIKLVKRLLK", "DE_NOVO",
         "Arg-Val alternating; irregular amphipathicity; low mu_h; non-helical mechanism"),
        ("SEED-019_VAR_002", "RVRIKFVKRLLK", "DE_NOVO",
         "Arg-Val alternating; F5→Phe aromatic; membrane insertion without helical mu_h"),
        ("SEED-019_VAR_003", "RVRIKLVKRALK", "DE_NOVO",
         "Arg-Val alternating; L11→A; reduced tail hydrophobicity"),
        ("SEED-019_VAR_004", "RVRIRLVKRLLK", "DE_NOVO",
         "Arg-Val alternating; K5→R; all-Arg cationic variant"),
        ("SEED-019_VAR_005", "RVRIKLVKRLLKK", "DE_NOVO",
         "Arg-Val alternating; C-terminal Lys extension; 13-mer"),
        ("SEED-019_VAR_006", "RVRIKFVKRALK", "DE_NOVO",
         "Arg-Val alternating; Phe + Ala tail; balanced aromatic/charge variant"),
        ("SEED-019_VAR_007", "RVRIKLVKRLLR", "DE_NOVO",
         "Arg-Val alternating; K12→R; all-Arg C-terminal"),
        ("SEED-019_VAR_008", "RVRIKLAKRLLK", "DE_NOVO",
         "Arg-Val alternating; V5→A; lower hydrophobicity de-risked variant"),
        ("SEED-019_VAR_009", "RVRIRLAKRLLK", "DE_NOVO",
         "Arg-Val alternating; K5→R + V6→A; dual substitution"),
        ("SEED-019_VAR_010", "RVRIKFVKRALK", "DE_NOVO",
         "Arg-Val alternating; F5 + A11; aromatic + de-risked tail"),
        ("SEED-019_VAR_011", "RVRIRLVKRALK", "DE_NOVO",
         "Arg-Val alternating; K5→R + A11; Arg-enriched de-risked"),
        ("SEED-019_VAR_012", "RVRIKIVKRLLK", "DE_NOVO",
         "Arg-Val alternating; F5→I; all-aliphatic hydrophobic face"),
    ]),
]


def _is_valid_sequence(seq: str) -> bool:
    return all(aa in VALID_AA for aa in seq) and 8 <= len(seq) <= 35


def main() -> None:
    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "wave0_5_raw_candidates.csv"

    fieldnames = [
        "candidate_id", "seed_family", "sequence", "length", "source_type",
        "generation_reason", "net_charge_pH74", "hydrophobic_fraction",
        "hydrophobic_moment", "aromatic_fraction", "boman_index",
        "initial_activity_score", "initial_safety_score", "novelty_proxy",
        "synthesis_flags",
    ]

    rows: list[dict] = []
    seen_seqs: set[str] = set()
    family_counts: dict[str, int] = {}

    for seed_id, candidates in FAMILIES:
        for cand_id, seq, source_type, reason in candidates:
            # Validity checks
            if not _is_valid_sequence(seq):
                print(f"WARNING: skipping {cand_id} — invalid sequence: {seq}")
                continue
            if seq in seen_seqs:
                print(f"WARNING: skipping {cand_id} — exact duplicate: {seq}")
                continue
            seen_seqs.add(seq)

            feats = compute_features(seq)
            act = activity_likeness_score(feats)
            safe = safety_score(feats)
            nov = novelty_proxy(seq)
            sf = synthesis_flags(seq, feats)
            boman = boman_index(seq)

            rows.append({
                "candidate_id": cand_id,
                "seed_family": seed_id,
                "sequence": seq,
                "length": feats["length"],
                "source_type": source_type,
                "generation_reason": reason,
                "net_charge_pH74": round(feats["net_charge_ph74"], 3),
                "hydrophobic_fraction": round(feats["hydrophobic_fraction"], 4),
                "hydrophobic_moment": round(feats["hydrophobic_moment"], 4),
                "aromatic_fraction": round(feats["aromatic_fraction"], 4),
                "boman_index": round(boman, 4),
                "initial_activity_score": round(act, 4),
                "initial_safety_score": round(safe, 4),
                "novelty_proxy": nov,
                "synthesis_flags": sf,
            })
            family_counts[seed_id] = family_counts.get(seed_id, 0) + 1

    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    n_families = len(family_counts)
    print(f"Generated {total} raw candidates across {n_families} new seed families.")
    print(f"Output: {out_path}")
    for fam, n in sorted(family_counts.items()):
        print(f"  {fam}: {n} candidates")

    # Validate acceptance criteria
    assert total >= 80, f"FAIL: only {total} candidates (need ≥80)"
    assert n_families >= 8, f"FAIL: only {n_families} families (need ≥8)"
    assert not any("C" in row["sequence"] and row["sequence"].count("C") >= 2
                   for row in rows), "FAIL: multi-Cys candidate slipped through"
    print("\nAll acceptance criteria MET.")


if __name__ == "__main__":
    main()
