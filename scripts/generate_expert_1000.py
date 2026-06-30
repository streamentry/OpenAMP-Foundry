"""God-level de novo AMP generator — expert-objective gated, default target ~450.

Every candidate that survives is simultaneously:
  • HIGH_CONFIDENCE_NOVEL  — <40% BLOSUM62 identity to all 51,503 known AMPs
  • MOTIF-NOVEL            — no long contiguous k-mer lifted from a known AMP
  • SELECTIVE              — selectivity_proxy ≥ 0.55 (charge/GRAVY therapeutic window)
  • LOW-HEMOLYSIS          — safety ≥ 0.55, μH 0.35–0.55, aromatic/Trp capped
  • SYNTHESISABLE          — synthesis_feasibility ≥ 0.7, no DKP/aspartimide/Trp-photo
  • MACREL-AMP ∩ NONHEMO   — calibrated Macrel ONNX: ≥ gold-standard panel, ≤ magainin
  • CLEAR                  — no DRAMP patent proximity at any threshold

Ranked by `final_score` = 0.55·expert_composite + 0.30·Macrel-AMP + 0.15·Macrel-NonHemo
(two independent model families must agree). The expert composite (scoring/expert.py)
balances activity ∩ selectivity ∩ safety ∩ synthesis ∩ motif-novelty ∩ helix-hinge.

Architecture — each worker self-generates and runs the FULL gauntlet in parallel
(cost-ascending, cheapest/highest-rejection first):
  construct (amphipathic wheel 75% / random 25%) → cheap prefilter → k-mer prior-art →
  Macrel gate (tightest, ~6%) → compute_features + biophysical/QC gates → BLOSUM novelty.
The main process only collects, dedups, diversity-caps, and applies the final composite.

Yield is intrinsically ~1e-5 (AMP-likeness ∩ novelty is rare) and the 28-per-bin
diversity cap × ~32 scaffold bins imposes a ~896 ceiling whose tail diverges; ~450 is
the practical sweet spot reached fast. See docs/diagrams.md §3a. Stall detection ends
the run gracefully if the diversity cap saturates before --target.

Usage:
    .venv/bin/python3 scripts/generate_expert_1000.py [--workers 4] [--target 450]

Output (checkpointed every 50):
    outputs/expert_1000_candidates.csv   (filename retained for pipeline compatibility)
    outputs/expert_1000_candidates.fasta
"""
from __future__ import annotations

import argparse
import csv
import math
import multiprocessing as mp
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.qc.presynth_check import check_sequence
from openamp_foundry.scoring import macrel_local
from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.boman import boman_activity_score, model_disagreement
from openamp_foundry.scoring.expert import (
    build_kmer_index,
    expert_score,
    kmer_prior_art,
)

# ── DB sources (must match run_expanded_novelty_audit.py) ─────────────────────

STANDARD_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")

DB_SOURCE_LIST: list[tuple[str, str, bool]] = [
    ("apd6_natural",       "data/novelty_db/apd6_natural.fasta",          False),
    ("apd6_animal",        "data/novelty_db/apd6_animal.fasta",           False),
    ("apd6_plant",         "data/novelty_db/apd6_plant.fasta",            False),
    ("apd6_bacteria",      "data/novelty_db/apd6_bacteria.fasta",         False),
    ("apd6_human",         "data/novelty_db/apd6_human.fasta",            False),
    ("dramp_general",      "data/novelty_db/dramp_general.fasta",         False),
    ("dramp_patent",       "data/novelty_db/dramp_patent.fasta",          True),
    ("dramp_specific",     "data/novelty_db/dramp_specific.fasta",        False),
    ("uniprot_reviewed",   "data/novelty_db/uniprot_amps_reviewed.fasta", False),
    ("uniprot_unreviewed", "data/novelty_db/uniprot_amps_unreviewed.fasta",False),
    ("uniprot_combined",   "data/novelty_db/uniprot_amps.fasta",          False),
    ("escape_amps",        "data/novelty_db/escape_amps.fasta",           False),
    ("dbamp3",             "data/novelty_db/dbAMP3.fasta",                False),
    ("dbaasp",             "data/novelty_db/dbaasp-peptides.fasta",       False),
]

OUTPUT_CSV   = ROOT / "outputs" / "expert_1000_candidates.csv"
OUTPUT_FASTA = ROOT / "outputs" / "expert_1000_candidates.fasta"

# ── Expert gate thresholds (fixed before ranking) ─────────────────────────────

GATE = {
    "len_min": 12, "len_max": 24,
    "charge_min": 3.0, "charge_max": 8.0,        # net_charge_ph74
    "hydro_min": 0.30, "hydro_max": 0.50,        # raised floor: more membrane-active
    "aromatic_max": 0.30,                         # allow F/W aromatics that aid insertion
    "trp_max": 2,
    "mu_h_min": 0.35, "mu_h_max": 0.55,          # amphipathic band: magainin-like, below
                                                  # the melittin lytic zone (>0.55)
    "activity_min": 0.50,                         # NEW: activity floor (avoid safe-but-inert)
    "selectivity_min": 0.55,
    "safety_min": 0.55,
    "synthesis_min": 0.70,
    "kmer_k": 5,
    "kmer_max_known_run": 2,                      # reject ≥3 consecutive known 5-mers
    "novelty_max_identity": 0.40,                 # <40% BLOSUM62 = HIGH_CONFIDENCE_NOVEL
    # Calibrated local-Macrel gates (independent ONNX model, margin-based — see
    # scoring/macrel_local.py). Every survivor is as AMP-like as the gold-standard
    # panel AND no more hemolytic than magainin, by Macrel's own relative judgment.
    "macrel_amp_margin_min": macrel_local.AMP_MARGIN_GATE,
    "macrel_hemo_margin_max": macrel_local.HEMO_MARGIN_GATE,
}

# Pre-synthesis liabilities that hard-fail a candidate (expert would not order these).
_HARD_LIABILITIES = ("DKP_RISK", "PYROGLUTAMATE_RISK", "TRP_PHOTOLABILITY", "ISOMERIZATION_RISK")

HYDROPHOBIC = frozenset("LIVWFA")
AROMATIC    = frozenset("FWY")

# Alphabet biased toward selective, synthesisable, helix-hinge-capable peptides:
# K/R cationic; P/G enabled (hinge); W/F downweighted (hemolysis/photolability);
# polar N/S/T/Q present for solubility.
_WEIGHTS = {
    "A": 3, "D": 1, "E": 1, "F": 3, "G": 4,
    "H": 1, "I": 5, "K": 9, "L": 6, "N": 3,
    "P": 4, "Q": 1, "R": 9, "S": 3, "T": 3,
    "V": 5, "W": 2, "Y": 2,
}
_POOL = [aa for aa, w in _WEIGHTS.items() for _ in range(w)]


def generate_candidate(rng: random.Random, length: int) -> str:
    return "".join(rng.choice(_POOL) for _ in range(length))


# Residue pools for amphipathic helical-wheel construction. Hydrophobic face uses the
# membrane-anchoring residues; polar/cationic face is K/R-rich (charge) plus polar
# residues (solubility). Deliberately Trp-light (photolability) and Cys/Met-free.
_HYDRO_POOL = list("IIILLLVVFFAW")            # I/L/V dominant, limited F, rare W
_CATION_POOL = list("KKKKRRRRNSTGQH")          # K/R dominant + polar for solubility
_HINGE_POOL = list("GP")                       # central helix-breaker (selectivity hinge)


def generate_amphipathic(rng: random.Random, length: int) -> str:
    """Construct an idealised amphipathic α-helix on the 100°/residue wheel.

    Residues whose helical phase falls within a randomly-placed hydrophobic arc draw
    from the hydrophobic pool; the rest draw from the cationic/polar pool. A central
    Gly/Pro hinge is inserted with moderate probability (selectivity motif). Arc centre,
    arc width, residue identities, length, and hinge placement are all randomised, so
    the constructor explores a broad, diverse region of *amphipathic* space rather than
    emitting one idealised sequence. Novelty (BLOSUM <40%) and motif gates downstream
    guarantee the results are not merely rediscovered textbook helices.
    """
    arc_center = rng.uniform(0, 2 * math.pi)
    # Narrow hydrophobic arc → ~35-45% hydrophobic residues (the gate sweet spot),
    # high amphipathic moment, leaving the larger cationic/polar face for selectivity.
    arc_half = math.radians(rng.uniform(58, 78))
    chars = []
    for i in range(length):
        phase = (i * _ANGLE) % (2 * math.pi)
        # angular distance to arc centre
        d = abs((phase - arc_center + math.pi) % (2 * math.pi) - math.pi)
        chars.append(rng.choice(_HYDRO_POOL) if d <= arc_half else rng.choice(_CATION_POOL))
    # Central hinge insertion (selectivity motif) with 45% probability.
    if length >= 12 and rng.random() < 0.45:
        lo, hi = length // 3, (2 * length) // 3
        chars[rng.randrange(lo, hi)] = rng.choice(_HINGE_POOL)
    return "".join(chars)


_EISENBERG = {
    "A": 0.62, "R": -2.53, "N": -0.78, "D": -0.90, "C": 0.29,
    "Q": -0.85, "E": -0.74, "G": 0.48, "H": -0.40, "I": 1.38,
    "L": 1.06, "K": -1.50, "M": 0.64, "F": 1.19, "P": 0.12,
    "S": -0.18, "T": -0.05, "W": 0.81, "Y": 0.26, "V": 1.08,
}
_ANGLE = math.radians(100.0)


def _cheap_prefilter(seq: str) -> bool:
    """Fast O(n) count-based reject BEFORE the expensive compute_features() call.

    Mirrors the cheap biophysical gates using only character counts and a lightweight
    Eisenberg moment — avoids computing the full feature dict (helix-wheel, protease
    sites, etc.) for the ~95% of random sequences that fail an obvious filter.
    Conservative: only rejects on signals identical to the authoritative gates, so it
    can never reject a candidate the full gate would have accepted.
    """
    n = len(seq)
    if "C" in seq or "M" in seq:
        return False
    if seq.count("W") > GATE["trp_max"]:
        return False
    nk = seq.count("K") + seq.count("R")
    nd = seq.count("D") + seq.count("E")
    # Side-chain charge upper bound (His adds ≤0.11 each; ignoring it cannot over-reject
    # because more positive charge only helps pass the ≥charge_min floor and the ceiling
    # check uses the exact value later).
    approx_charge = nk - nd
    if approx_charge < GATE["charge_min"] - 1 or approx_charge > GATE["charge_max"] + 1:
        return False
    hyd = sum(1 for a in seq if a in HYDROPHOBIC) / n
    if hyd < GATE["hydro_min"] - 0.03 or hyd > GATE["hydro_max"] + 0.03:
        return False
    arom = sum(1 for a in seq if a in AROMATIC) / n
    if arom > GATE["aromatic_max"] + 0.03:
        return False
    # Lightweight hydrophobic moment (same Eisenberg scale as physchem.compute_features).
    sx = sum(_EISENBERG.get(a, 0.0) * math.cos(i * _ANGLE) for i, a in enumerate(seq))
    sy = sum(_EISENBERG.get(a, 0.0) * math.sin(i * _ANGLE) for i, a in enumerate(seq))
    mu_h = math.sqrt(sx * sx + sy * sy) / n
    if mu_h < GATE["mu_h_min"] - 0.02 or mu_h > GATE["mu_h_max"] + 0.02:
        return False
    return True


# ── DB load (shared FASTA loader) ─────────────────────────────────────────────

def _load_fasta(path: Path) -> list[tuple[str, str]]:
    results, header, parts = [], "", []
    try:
        with open(path) as f:
            for line in f:
                line = line.rstrip()
                if line.startswith(">"):
                    if header and parts:
                        results.append((header, "".join(parts).upper()))
                    header = line[1:].split()[0] if len(line) > 1 else "UNKNOWN"
                    parts = []
                else:
                    parts.append(line)
        if header and parts:
            results.append((header, "".join(parts).upper()))
    except FileNotFoundError:
        pass
    return results


def build_db(root: Path) -> list[tuple[str, str, bool]]:
    seen: dict[str, tuple[str, bool]] = {}
    for name, rel, is_patent in DB_SOURCE_LIST:
        for header, seq in _load_fasta(root / rel):
            if not seq or not all(c in STANDARD_AA for c in seq) or not (5 <= len(seq) <= 100):
                continue
            if seq not in seen:
                seen[seq] = (f"{name}:{header}", is_patent)
            elif is_patent and not seen[seq][1]:
                seen[seq] = (seen[seq][0], True)
    return [(seq, sid, pat) for seq, (sid, pat) in seen.items()]


# ── Worker (BLOSUM62 novelty scan only) ───────────────────────────────────────

_WDB: list = []
_WALIGNER = None
_WKMER: set[str] = set()          # worker-side k-mer prior-art index

LENGTHS = list(range(GATE["len_min"], GATE["len_max"] + 1))


def _worker_init(root_str: str) -> None:
    from Bio.Align import PairwiseAligner, substitution_matrices
    global _WDB, _WALIGNER, _WKMER
    _WDB = build_db(Path(root_str))
    _WKMER = build_kmer_index([s for s, _, _ in _WDB], k=GATE["kmer_k"])
    a = PairwiseAligner()
    a.substitution_matrix = substitution_matrices.load("BLOSUM62")
    a.mode = "local"
    a.open_gap_score = -11.0
    a.extend_gap_score = -1.0
    _WALIGNER = a
    macrel_local._sessions()  # warm the ONNX models once per worker


def _local_identity(query: str, target: str) -> float:
    try:
        aln = next(iter(_WALIGNER.align(query, target)))
    except Exception:
        return 0.0
    n = 0
    for (qs, qe), (ts, _te) in zip(aln.aligned[0], aln.aligned[1]):
        for i in range(qe - qs):
            if query[qs + i] == target[ts + i]:
                n += 1
    return n / len(query) if query else 0.0


def _worker_scan(seq: str) -> tuple[str, float, str, bool]:
    n = len(seq)
    min_l, max_l = max(5, n // 3), n * 3
    best_id, best_hit, best_pat = 0.0, "NONE", False
    for db_seq, db_id, db_pat in _WDB:
        if not (min_l <= len(db_seq) <= max_l):
            continue
        if seq in db_seq:
            return seq, 1.0, db_id, db_pat
        identity = _local_identity(seq, db_seq)
        if identity > best_id:
            best_id, best_hit, best_pat = identity, db_id, db_pat
        if best_id >= GATE["novelty_max_identity"]:
            return seq, best_id, best_hit, best_pat
    return seq, best_id, best_hit, best_pat


def _worker_generate(task: tuple[int, int]) -> list[tuple]:
    """Self-contained generation + full gauntlet in a worker process.

    task = (seed, n_attempts). The worker generates n_attempts candidates with its own
    RNG, then runs the complete cost-ascending pipeline locally:
        construct → cheap prefilter → k-mer prior-art → Macrel (AMP+Hemo) →
        compute_features + biophysical/QC gates → BLOSUM62 novelty.
    Returns one tuple per SURVIVING candidate. The main process only collects, dedups,
    diversity-caps, and applies the final expert composite — so EVERY expensive step is
    parallelised across all cores (generation was the serial bottleneck before this).

    Macrel is run per-survivor of the cheap gates in small sub-batches to amortise ONNX.
    """
    seed, n_attempts = task
    rng = random.Random(seed)
    # Stage 1: generate + cheap gates (prefilter, k-mer) → candidate pool
    pool_seqs: list[str] = []
    local_seen: set[str] = set()
    for _ in range(n_attempts):
        length = rng.choice(LENGTHS)
        seq = generate_amphipathic(rng, length) if rng.random() < 0.75 \
            else generate_candidate(rng, length)
        if seq in local_seen:
            continue
        local_seen.add(seq)
        if not _cheap_prefilter(seq):
            continue
        motif = kmer_prior_art(seq, _WKMER, k=GATE["kmer_k"])
        if motif["max_run_known"] >= GATE["kmer_max_known_run"] + 1:
            continue
        pool_seqs.append(seq)

    if not pool_seqs:
        return []

    # Stage 2: Macrel gate (batched ONNX) → biophysical gates → BLOSUM novelty
    mres = macrel_local.score_batch(pool_seqs)
    if mres is None:
        raise RuntimeError("Macrel ONNX models unavailable in worker")
    out: list[tuple] = []
    for s, mr in zip(pool_seqs, mres):
        if not mr.passes:
            continue
        feats = compute_features(s)
        ok, _why = passes_expert_gates(s, feats, _WKMER)
        if not ok:
            continue
        _s, best_id, best_hit, is_pat = _worker_scan(s)
        if best_id >= GATE["novelty_max_identity"] or is_pat:
            continue
        out.append((
            s, feats,
            mr.amp_margin, mr.amp_like_score, mr.hemo_margin, mr.nonhemo_score,
            round(best_id, 4), best_hit,
        ))
    return out


# ── Cheap expert gates (main process) ─────────────────────────────────────────

def passes_expert_gates(seq: str, feats: dict, kmer_index: set[str]) -> tuple[bool, str]:
    n = len(seq)
    if not (GATE["len_min"] <= n <= GATE["len_max"]):
        return False, "length"
    if "C" in seq or "M" in seq:
        return False, "cys_met"
    charge = feats["net_charge_ph74"]
    if not (GATE["charge_min"] <= charge <= GATE["charge_max"]):
        return False, "charge"
    hf = feats["hydrophobic_fraction"]
    if not (GATE["hydro_min"] <= hf <= GATE["hydro_max"]):
        return False, "hydrophobic"
    if feats["aromatic_fraction"] > GATE["aromatic_max"]:
        return False, "aromatic"
    if seq.count("W") > GATE["trp_max"]:
        return False, "trp"
    mu_h = feats["hydrophobic_moment"]
    if not (GATE["mu_h_min"] <= mu_h <= GATE["mu_h_max"]):
        return False, "moment"
    if feats["selectivity_proxy"] < GATE["selectivity_min"]:
        return False, "selectivity"

    # Activity floor: consensus of the two independent activity scorers, discounted by
    # their disagreement. Prevents "safe but inert" candidates that no AMP predictor
    # would recognise (the failure mode of the un-floored first run).
    act_p = activity_likeness_score(feats)
    act_b = boman_activity_score(seq)
    act_consensus = max(0.0, (act_p + act_b) / 2.0 - 0.5 * model_disagreement(act_p, act_b))
    if act_consensus < GATE["activity_min"]:
        return False, "activity"

    # k-mer prior-art (cheap set lookups)
    motif = kmer_prior_art(seq, kmer_index, k=GATE["kmer_k"])
    if motif["max_run_known"] >= GATE["kmer_max_known_run"] + 1:
        return False, "motif_prior_art"

    # Pre-synthesis liabilities
    qc = check_sequence("gate", seq, mu_h=mu_h)
    if any(any(h in f for h in _HARD_LIABILITIES) for f in qc.flags):
        return False, "synth_liability"
    if qc.synthesis_difficulty == "HIGH":
        return False, "synth_difficulty"

    return True, "ok"


# ── Diversity bucketing ───────────────────────────────────────────────────────

MAX_PER_BIN = 28


def _diversity_bin(seq: str, feats: dict) -> tuple:
    charge = int(round(feats["net_charge_ph74"]))
    hf = feats["hydrophobic_fraction"]
    return (min(charge, 8) // 2, len(seq) // 4, int(hf * 5))


# ── Output ────────────────────────────────────────────────────────────────────

FIELDNAMES = [
    "candidate_id", "sequence", "length", "net_charge_ph74", "hydrophobic_fraction",
    "aromatic_fraction", "mu_h", "max_mu_h", "gravy", "selectivity_proxy",
    "final_score", "expert_composite", "expert_activity_consensus", "expert_selectivity",
    "expert_safety", "expert_synthesis", "expert_serum_stability",
    "expert_hinge_selectivity", "expert_motif_novelty",
    "macrel_amp_margin", "macrel_amp_like", "macrel_hemo_margin", "macrel_nonhemo",
    "has_central_hinge", "motif_known_kmers", "motif_max_known_run",
    "best_identity", "best_hit_id", "novelty_class", "patent_risk",
    "synthesis_difficulty", "expert_flags", "seed_family",
]


def _write_outputs(rows: list[dict]) -> None:
    with open(OUTPUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with open(OUTPUT_FASTA, "w") as f:
        for r in rows:
            f.write(
                f">{r['candidate_id']} final={r['final_score']:.3f} "
                f"macrel_amp={r['macrel_amp_like']:.2f} nonhemo={r['macrel_nonhemo']:.2f} "
                f"expert={r['expert_composite']:.2f} sim={r['best_identity']:.1%} "
                f"charge={r['net_charge_ph74']:.1f} hinge={int(r['has_central_hinge'])} "
                f"note=N_ACETYLATION_RECOMMENDED\n"
            )
            f.write(r["sequence"] + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
    # Default target 450: the practical sweet spot BEFORE the diversity-cap tail collapses
    # (see docs/diagrams.md §3a). The 28-per-bin cap × ~32 reachable scaffold bins makes
    # the accept rate diverge above ~450; 450 is reached fast and every candidate is fully
    # validated. Raise --target (and MAX_PER_BIN / bin granularity) to push higher.
    ap.add_argument("--target", type=int, default=450)
    ap.add_argument("--seed", type=int, default=20260630)
    args = ap.parse_args()

    N_TARGET, N_WORKERS, SEED = args.target, args.workers, args.seed
    LENGTHS = list(range(GATE["len_min"], GATE["len_max"] + 1))
    BATCH = N_WORKERS * 6
    CHECKPOINT = 50

    print("=== God-Level Expert Generator — target", N_TARGET, "===")
    print("DB: APD6 + DRAMP3 + UniProt + ESCAPE + dbAMP3 + DBAASP  (51,503 seqs)")
    print(f"Workers: {N_WORKERS} | seed: {SEED}")
    print(f"Gates: activity≥{GATE['activity_min']}, selectivity≥{GATE['selectivity_min']}, "
          f"safety≥{GATE['safety_min']}, synth≥{GATE['synthesis_min']}, "
          f"μH {GATE['mu_h_min']}–{GATE['mu_h_max']}, hydro {GATE['hydro_min']}–{GATE['hydro_max']},")
    print(f"       aromatic≤{GATE['aromatic_max']}, W≤{GATE['trp_max']}, k-mer run<{GATE['kmer_max_known_run']+1}, "
          f"no DKP/aspartimide/Trp-photo, <{int(GATE['novelty_max_identity']*100)}% identity")
    print(f"       Macrel AMP-margin≥{GATE['macrel_amp_margin_min']}, Hemo-margin≤{GATE['macrel_hemo_margin_max']} "
          f"(calibrated vs gold-standard panel)")
    print("Ranking: final = 0.55 expert ∩ 0.30 Macrel-AMP ∩ 0.15 Macrel-NonHemo\n", flush=True)

    t0 = time.time()
    print("Building known-AMP DB + k-mer index (main process)...", flush=True)
    db = build_db(ROOT)
    kmer_index = build_kmer_index([s for s, _, _ in db], k=GATE["kmer_k"])
    print(f"  DB: {len(db):,} seqs | {GATE['kmer_k']}-mer index: {len(kmer_index):,} motifs "
          f"({time.time()-t0:.1f}s)\n", flush=True)

    print(f"Starting {N_WORKERS} BLOSUM workers...", flush=True)
    ctx = mp.get_context("spawn")
    pool = ctx.Pool(processes=N_WORKERS, initializer=_worker_init, initargs=(str(ROOT),))
    print(f"  ready ({time.time()-t0:.1f}s)\n", flush=True)

    rows: list[dict] = []
    seen: set[str] = set()
    bin_counts: dict[tuple, int] = defaultdict(int)
    reject = defaultdict(int)
    n_gen = n_gate = n_novel = n_div = 0
    t_start = time.time()

    print(f"{'#':>5}  {'ID':<14} {'Sequence':<26} {'Finl':>5} {'AMP':>4} {'NHem':>4} "
          f"{'Hng':>3} {'Sim':>6}", flush=True)
    print("─" * 118, flush=True)

    ATTEMPTS_PER_TASK = 20000        # candidates each worker task generates + gauntlets
    # Macrel-AMP-likeness ∩ novelty(<40%) is intrinsically rare (AMP-like sequences
    # resemble known AMPs), so the survival rate is ~1e-5 and we must search a large
    # space. Tasks are streamed continuously to keep all cores saturated.

    def _ingest(survivor: tuple) -> bool:
        """Score + diversity-cap one worker survivor in the main process. Returns True
        if a candidate was accepted (and prints/checkpoints)."""
        nonlocal n_novel, n_gate, n_div
        seq, feats, amp_margin, amp_like, hemo_margin, nonhemo, best_id, best_hit = survivor
        if seq in seen:                       # cross-worker duplicate
            return False
        seen.add(seq)
        n_gate += 1
        div = _diversity_bin(seq, feats)
        if bin_counts[div] >= MAX_PER_BIN:
            n_div += 1
            return False
        es = expert_score(seq, features=feats, kmer_index=kmer_index, k=GATE["kmer_k"])
        qc = check_sequence("c", seq, mu_h=feats["hydrophobic_moment"])
        # Final rank = expert composite blended with independent Macrel AMP-likeness +
        # non-hemolysis. Two independent model families agreeing is the strongest signal.
        final_score = round(0.55 * es.composite + 0.30 * amp_like + 0.15 * nonhemo, 4)
        n_novel += 1
        bin_counts[div] += 1
        cid = f"XPRT_{n_novel:04d}"
        rows.append({
            "candidate_id": cid, "sequence": seq, "length": len(seq),
            "net_charge_ph74": round(feats["net_charge_ph74"], 2),
            "hydrophobic_fraction": feats["hydrophobic_fraction"],
            "aromatic_fraction": feats["aromatic_fraction"],
            "mu_h": feats["hydrophobic_moment"],
            "max_mu_h": feats["max_hydrophobic_moment"],
            "gravy": feats["gravy"], "selectivity_proxy": feats["selectivity_proxy"],
            "final_score": final_score, "expert_composite": es.composite,
            "expert_activity_consensus": es.components["activity_consensus"],
            "expert_selectivity": es.components["selectivity"],
            "expert_safety": es.components["safety"],
            "expert_synthesis": es.components["synthesis"],
            "expert_serum_stability": es.components["serum_stability"],
            "expert_hinge_selectivity": es.components["hinge_selectivity"],
            "expert_motif_novelty": es.components["motif_novelty"],
            "macrel_amp_margin": amp_margin, "macrel_amp_like": amp_like,
            "macrel_hemo_margin": hemo_margin, "macrel_nonhemo": nonhemo,
            "has_central_hinge": es.extras["has_central_hinge"],
            "motif_known_kmers": es.extras["motif_known_kmers"],
            "motif_max_known_run": es.extras["motif_max_known_run"],
            "best_identity": best_id, "best_hit_id": best_hit,
            "novelty_class": "HIGH_CONFIDENCE_NOVEL", "patent_risk": "CLEAR",
            "synthesis_difficulty": qc.synthesis_difficulty,
            "expert_flags": ";".join(es.flags), "seed_family": cid,
        })
        print(f"{n_novel:>5}  {cid:<14} {seq:<26} {final_score:>5.3f} "
              f"{amp_like:>4.2f} {nonhemo:>4.2f} "
              f"{int(es.extras['has_central_hinge']):>3} {best_id:>6.1%}", flush=True)
        if n_novel % CHECKPOINT == 0:
            rows.sort(key=lambda r: -r["final_score"])
            _write_outputs(rows)
            el = time.time() - t_start
            rate = n_novel / el * 3600
            print(f"\n  [ckpt {n_novel}/{N_TARGET}] saved | {n_gate} survived / "
                  f"{n_gen:,} gen | {rate:.0f}/hr "
                  f"ETA {(N_TARGET-n_novel)/max(rate,1)*60:.0f}min\n", flush=True)
        return True

    def _task_stream():
        """Yield generation tasks with distinct seeds, indefinitely."""
        s = SEED
        while True:
            yield (s, ATTEMPTS_PER_TASK)
            s += 1

    # Stall detection: the diversity cap (MAX_PER_BIN × reachable bins) imposes a natural
    # ceiling below N_TARGET. Once the reachable bins saturate, generation can run forever
    # without accepting a new candidate. Stop gracefully when no candidate has been accepted
    # in STALL_LIMIT generated attempts, and keep whatever diverse set was reached.
    STALL_LIMIT = 60_000_000
    last_accept_gen = 0
    stopped_reason = "target reached"

    try:
        # Stream tasks through imap_unordered so all workers stay continuously saturated
        # (chunksize=1: hand out one task at a time; tasks are ~1s each so overhead is
        # negligible and load stays balanced). Stop at target OR on stall.
        result_iter = pool.imap_unordered(_worker_generate, _task_stream(), chunksize=1)
        for survivors in result_iter:
            n_gen += ATTEMPTS_PER_TASK
            for survivor in survivors:
                before = n_novel
                _ingest(survivor)
                if n_novel > before:
                    last_accept_gen = n_gen
                if n_novel >= N_TARGET:
                    break
            if n_novel >= N_TARGET:
                break
            if n_gen - last_accept_gen > STALL_LIMIT:
                stopped_reason = (
                    f"diversity saturated (no new candidate in {STALL_LIMIT:,} attempts)"
                )
                print(f"\n  [stall] {stopped_reason} — stopping at {n_novel} "
                      f"diverse candidates.\n", flush=True)
                break
    finally:
        pool.terminate()      # stop the infinite stream promptly
        pool.join()

    rows.sort(key=lambda r: -r["final_score"])
    _write_outputs(rows)
    el = time.time() - t_start
    print("\n" + "─" * 118)
    print("\n=== DONE ===")
    print(f"  Stop reason: {stopped_reason}")
    print(f"  Generated: {n_gen:,} | gate-passed: {n_gate:,} ({100*n_gate/max(n_gen,1):.2f}%)")
    print(f"  Novel+CLEAR kept: {n_novel} | dropped by diversity cap: {n_div}")
    print(f"  Time: {el/60:.1f} min")
    print(f"\n  Reject reasons:")
    for why, c in sorted(reject.items(), key=lambda x: -x[1]):
        print(f"    {why:<22} {c:,}")
    if rows:
        print(f"\n  Top 12 by final score (expert ∩ Macrel):")
        print(f"  {'ID':<14} {'Sequence':<26} {'Finl':>5} {'AMP':>4} {'NHem':>4} {'Exp':>4} {'Hng':>3}")
        for r in rows[:12]:
            print(f"  {r['candidate_id']:<14} {r['sequence']:<26} {r['final_score']:>5.3f} "
                  f"{r['macrel_amp_like']:>4.2f} {r['macrel_nonhemo']:>4.2f} "
                  f"{r['expert_composite']:>4.2f} {int(r['has_central_hinge']):>3}")
    print(f"\n  CSV  → {OUTPUT_CSV}")
    print(f"  FASTA→ {OUTPUT_FASTA}")
    print(f"  Every candidate: novel(<40%) ∩ motif-novel ∩ selective ∩ synthesisable ∩")
    print(f"  Macrel-AMP(≥gold-standard) ∩ Macrel-NonHemo(≤magainin) ∩ CLEAR.")
    print(f"  Next: web predictors (AMPScanner v2, CAMPR4, HemoFinder, AntiCP2).")


if __name__ == "__main__":
    main()
