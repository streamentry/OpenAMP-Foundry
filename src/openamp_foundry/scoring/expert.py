"""Expert composite scorer — fuses the full OpenAMP toolkit into one objective.

The individual scorers (activity, safety, synthesis, selectivity, Boman, serum
stability, pre-synthesis QC) each capture one axis a domain expert reasons about.
In isolation, optimising any single axis produces pathological candidates: maximise
`activity_likeness` alone and you get melittin-like hemolytic helices; maximise
`novelty` alone and you get unsynthesisable junk. A 30-year peptide chemist does not
rank by one number — they hold *activity AND selectivity AND synthesisability AND
genuine novelty* simultaneously, and they recognise two things our per-axis scorers
historically missed:

  1. **Central helix-hinge selectivity.** A single helix-breaking residue (Gly/Pro)
     near the centre of an otherwise amphipathic cationic helix is a recurring motif
     in selective natural AMPs (cecropin A's Gly23-Pro24 hinge; the bent-helix class).
     The hinge interrupts the rigid continuous amphipathic helix that most efficiently
     lyses *zwitterionic mammalian* membranes, while preserving the cationic attraction
     to *anionic bacterial* membranes — improving the therapeutic window. A flat
     hydrophobic-moment number cannot see "break at position N".
     References: Tossi, Sandri & Giangaspero (2000) Biopolymers 55:4-30;
     Shai (2002) Biopolymers 66:236-248; Saberwal & Nagaraj (1994) BBA 1197:109-131.

  2. **Motif-level prior art.** Global BLOSUM identity can read <40% while the peptide
     still contains a contiguous k-mer lifted straight from a known AMP — the local
     motif an expert recognises on sight. Exact k-mer overlap against the full known-AMP
     corpus automates that recognition and is strictly sharper than a global-identity
     gate for catching "this looks like X".

This module is transparent and heuristic. It makes NO validated biological claim.
Every weight and threshold is documented and fixed before candidate ranking. The
output is a full component breakdown plus a single composite so selection is auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.activity import activity_likeness_score, clamp01
from openamp_foundry.scoring.boman import boman_activity_score, model_disagreement
from openamp_foundry.scoring.safety import safety_score
from openamp_foundry.scoring.hemolysis import hemolysis_safety_component
from openamp_foundry.scoring.selectivity_rich import rich_selectivity_score
from openamp_foundry.scoring.stability import serum_stability_score
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score

# Residues that break an α-helix (Chou-Fasman Pα ≈ 0.57, the two canonical breakers).
_HELIX_BREAKERS = frozenset("GP")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Central helix-hinge selectivity
# ─────────────────────────────────────────────────────────────────────────────

def helix_hinge_analysis(sequence: str) -> dict:
    """Detect a central helix-breaking hinge (Gly/Pro) and score its selectivity value.

    Biological rationale: in amphipathic cationic AMPs, a single helix-breaker located
    in the central third of the sequence introduces a flexible kink between two shorter
    helical segments. This "hinged" architecture (cecropin A, the bent-helix class) is
    associated with *improved bacterial-vs-mammalian selectivity* — the discontinuous
    helix is a less efficient pore-former in zwitterionic mammalian membranes while
    retaining cationic attraction to anionic bacterial surfaces.

    Scoring (hinge_score ∈ [0, 1]):
      - Exactly one breaker in the central third          → 1.00 (ideal single hinge)
      - Two breakers in the central third                 → 0.60 (over-flexible)
      - Zero central breakers                             → 0.30 (rigid helix; neutral)
      - Three+ central breakers, or any breaker run ≥2    → 0.10 (helix destroyed)

    The central third is defined as indices [n//3, 2*n//3). Terminal Gly/Pro are NOT
    hinges — N/C-terminal flexibility does not produce the selectivity-relevant central
    kink, and terminal Pro/Gly carry their own (separately handled) liabilities.

    Returns dict with: central_breakers, central_breaker_positions (1-based),
    has_central_hinge, breaker_run, hinge_score.

    References: Tossi et al. (2000) Biopolymers 55:4-30; Shai (2002) Biopolymers 66:236;
    Saberwal & Nagaraj (1994) BBA 1197:109-131.
    """
    n = len(sequence)
    if n < 6:
        return {
            "central_breakers": 0,
            "central_breaker_positions": [],
            "has_central_hinge": False,
            "breaker_run": 0,
            "hinge_score": 0.0,
        }

    lo, hi = n // 3, (2 * n) // 3
    positions = [i + 1 for i in range(lo, hi) if sequence[i] in _HELIX_BREAKERS]
    n_central = len(positions)

    # Longest consecutive run of breakers anywhere (a PP/GG/PG run shreds the helix).
    breaker_run = 0
    current = 0
    for aa in sequence:
        if aa in _HELIX_BREAKERS:
            current += 1
            breaker_run = max(breaker_run, current)
        else:
            current = 0

    if breaker_run >= 2:
        hinge_score = 0.10
    elif n_central == 1:
        hinge_score = 1.00
    elif n_central == 2:
        hinge_score = 0.60
    elif n_central == 0:
        hinge_score = 0.30
    else:  # 3+ isolated central breakers
        hinge_score = 0.10

    return {
        "central_breakers": n_central,
        "central_breaker_positions": positions,
        "has_central_hinge": n_central == 1 and breaker_run < 2,
        "breaker_run": breaker_run,
        "hinge_score": round(hinge_score, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Motif-level (k-mer) prior art
# ─────────────────────────────────────────────────────────────────────────────

def build_kmer_index(sequences: list[str], k: int = 5) -> set[str]:
    """Build the set of all contiguous k-mers present in a corpus of known sequences.

    Built once over the full known-AMP corpus, then queried per candidate. With k=5
    over a 20-letter alphabet there are 20^5 = 3.2M possible k-mers; a ~51k-sequence
    corpus realises ~1–1.5M of them, so a chance 5-mer collision for a random peptide
    is ~30–45% per k-mer — informative but not saturating. k=5 is the standard local
    "word" length used by BLASTp seeding for short proteins.
    """
    index: set[str] = set()
    for seq in sequences:
        s = seq.upper()
        for i in range(len(s) - k + 1):
            index.add(s[i : i + k])
    return index


def kmer_prior_art(sequence: str, kmer_index: set[str], k: int = 5) -> dict:
    """Quantify how much of a candidate's local motif content is lifted from known AMPs.

    Complements global BLOSUM identity: a candidate can read <40% global identity yet
    still embed a contiguous k-mer copied verbatim from a known AMP — the local motif a
    trained eye recognises. We count the candidate's k-mers that appear anywhere in the
    known-AMP corpus.

    motif_novelty_score ∈ [0, 1] (higher = more locally novel):
      - 1.00 → no k-mer of the candidate appears in any known AMP (fully novel motifs)
      - 0.00 → every k-mer is found in the corpus (locally derivative despite low identity)

    The score is the fraction of k-mers NOT found in the corpus. `max_run_known` reports
    the longest stretch of consecutive known k-mers (a contiguous lifted segment is a
    stronger prior-art signal than the same number of scattered hits).

    Returns: n_kmers, n_known, novel_fraction, max_run_known, motif_novelty_score.
    """
    s = sequence.upper()
    n_kmers = len(s) - k + 1
    if n_kmers <= 0:
        return {
            "n_kmers": 0, "n_known": 0, "novel_fraction": 1.0,
            "max_run_known": 0, "motif_novelty_score": 1.0,
        }

    known_flags = [s[i : i + k] in kmer_index for i in range(n_kmers)]
    n_known = sum(known_flags)

    max_run = run = 0
    for flag in known_flags:
        if flag:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0

    novel_fraction = (n_kmers - n_known) / n_kmers
    return {
        "n_kmers": n_kmers,
        "n_known": n_known,
        "novel_fraction": round(novel_fraction, 4),
        "max_run_known": max_run,
        "motif_novelty_score": round(novel_fraction, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Expert composite
# ─────────────────────────────────────────────────────────────────────────────

# Component weights. Fixed before ranking. Sum = 1.00.
# Deliberately balanced AWAY from raw activity toward selectivity + safety, because the
# dominant empirical failure of naive AMP generation is hemolysis, not lack of potency:
# predictors are easy to satisfy on "is it an AMP", hard on "will it spare host cells".
EXPERT_WEIGHTS: dict[str, float] = {
    "activity_consensus": 0.20,   # physchem ∩ Boman agreement (penalised by disagreement)
    "selectivity":        0.20,   # charge/GRAVY therapeutic-window proxy (AMP-vs-decoy signal)
    "safety":             0.15,   # hemolysis-risk proxy (μH, hydrophobicity, charge density)
    "synthesis":          0.12,   # SPPS feasibility (length, repeats, aggregation, Pro)
    "serum_stability":    0.05,   # proteolytic longevity (informational, low weight)
    "hinge_selectivity":  0.08,   # central helix-hinge bonus (expert motif)
    "motif_novelty":      0.10,   # k-mer prior-art (local novelty beyond global identity)
    "rich_selectivity":   0.10,   # evidence-based 8-feature hemolysis detector (AUROC=0.7138, CI 0.63-0.80, significant)
}


@dataclass
class ExpertScore:
    """Transparent expert composite with full component breakdown."""

    sequence: str
    composite: float
    components: dict[str, float]
    extras: dict[str, float] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        out = {"sequence": self.sequence, "expert_composite": self.composite}
        out.update({f"expert_{k}": v for k, v in self.components.items()})
        out.update(self.extras)
        out["expert_flags"] = ";".join(self.flags) if self.flags else ""
        return out


def expert_score(
    sequence: str,
    *,
    features: dict | None = None,
    kmer_index: set[str] | None = None,
    k: int = 5,
    weights: dict[str, float] | None = None,
) -> ExpertScore:
    """Compute the transparent expert composite for one peptide.

    Args:
        sequence: peptide (canonical AA, uppercase).
        features: optional precomputed compute_features() dict (recomputed if None).
        kmer_index: optional known-AMP k-mer set for motif-novelty (skipped if None,
            in which case motif_novelty defaults to 1.0 and is still weighted — pass
            an index whenever motif-level prior art matters, e.g. during generation).
        k: k-mer length (default 5).
        weights: optional weight override (defaults to EXPERT_WEIGHTS).

    Returns ExpertScore with .composite ∈ [0,1] and a full component/extra breakdown.
    """
    seq = sequence.upper()
    feats = features if features is not None else compute_features(seq)
    w = weights or EXPERT_WEIGHTS

    # Activity consensus: mean of the two independent activity scorers, then discounted
    # by their disagreement (an explicit uncertainty penalty — agreeing scorers are
    # more trustworthy than a single optimistic one).
    act_physchem = activity_likeness_score(feats)
    act_boman = boman_activity_score(seq)
    disagreement = model_disagreement(act_physchem, act_boman)
    activity_consensus = clamp01((act_physchem + act_boman) / 2.0 - 0.5 * disagreement)

    # selectivity_proxy: charge/GRAVY therapeutic-window proxy. Not significant for
    # hemolysis detection (AUROC=0.5744, CI 0.50-0.66) but contributes to AMP-vs-decoy
    # ranking (strict triage AUROC=0.500 — composition-driven, not harmful).
    selectivity = float(feats.get("selectivity_proxy", 0.0))
    # Rich selectivity (v0.5.16): evidence-based composite of 8 significant features.
    # Detection AUROC=0.7138 (CI 0.63-0.80) — first pipeline score with CI excluding
    # 0.5 for selective_vs_hemolytic. Replaces hemolysis_safety (AUROC=0.565, not
    # significant) as the primary hemolysis-risk component in the expert composite.
    rich_sel = rich_selectivity_score(feats)
    safety = safety_score(feats)
    synthesis = synthesis_feasibility_score(feats, valid_sequence=True)
    serum = serum_stability_score(feats)
    hemo_safety = hemolysis_safety_component(feats)

    hinge = helix_hinge_analysis(seq)
    hinge_selectivity = hinge["hinge_score"]

    if kmer_index is not None:
        motif = kmer_prior_art(seq, kmer_index, k=k)
        motif_novelty = motif["motif_novelty_score"]
    else:
        motif = {"n_known": 0, "max_run_known": 0, "motif_novelty_score": 1.0}
        motif_novelty = 1.0

    components = {
        "activity_consensus": round(activity_consensus, 4),
        "selectivity":        round(selectivity, 4),
        "safety":             round(safety, 4),
        "synthesis":          round(synthesis, 4),
        "serum_stability":    round(serum, 4),
        "hinge_selectivity":  round(hinge_selectivity, 4),
        "motif_novelty":      round(motif_novelty, 4),
        "rich_selectivity":   round(rich_sel, 4),
    }

    total_w = sum(w.values()) or 1.0
    composite = sum(components[name] * wt for name, wt in w.items()) / total_w
    composite = round(clamp01(composite), 4)

    extras = {
        "activity_physchem": act_physchem,
        "activity_boman": act_boman,
        "activity_disagreement": disagreement,
        "mu_h": float(feats.get("hydrophobic_moment", 0.0)),
        "max_mu_h": float(feats.get("max_hydrophobic_moment", 0.0)),
        "gravy": float(feats.get("gravy", 0.0)),
        "net_charge_ph74": float(feats.get("net_charge_ph74", 0.0)),
        "boman_index": float(feats.get("boman_index", 0.0)),
        "has_central_hinge": hinge["has_central_hinge"],
        "central_breakers": hinge["central_breakers"],
        "motif_known_kmers": motif["n_known"],
        "motif_max_known_run": motif["max_run_known"],
        "hemolysis_safety_legacy": round(hemo_safety, 4),
    }

    flags: list[str] = []
    if motif["max_run_known"] >= 3:
        flags.append(f"MOTIF_PRIOR_ART: {motif['max_run_known']} consecutive known {k}-mers")
    if hinge["breaker_run"] >= 2:
        flags.append("HELIX_DISRUPTED: consecutive Gly/Pro run breaks the helix")
    if disagreement >= 0.30:
        flags.append(f"ACTIVITY_DISAGREEMENT: physchem vs Boman differ by {disagreement:.2f}")

    return ExpertScore(
        sequence=seq,
        composite=composite,
        components=components,
        extras=extras,
        flags=flags,
    )
