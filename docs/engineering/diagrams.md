# OpenAMP Foundry — Pipeline Diagrams & Expert Reasoning

> **Purpose.** A single source of truth for *how* the dry-lab pipeline turns random
> sequence space into a small set of synthesis-ready, novel, selective antimicrobial
> peptide (AMP) candidates — and *why* each stage exists. Written to be defensible to a
> peptide chemist, a computational biologist, and an IP attorney simultaneously.
>
> **Honest framing.** Every score here is a *transparent heuristic*, not a validated
> biological predictor. The pipeline's job is to **narrow 10⁷ → ~10¹ with an auditable
> trail**, not to claim discovery. Discovery requires wet-lab confirmation. Nothing in
> this document asserts a candidate *works* — only that it survives every cheap filter
> a domain expert would apply before spending money on synthesis.

---

## 1. The Core Problem (why this is hard)

```
                  Sequence space for a 12–24-mer peptide
                  ≈ 20^18  ≈ 10^23 possible sequences
                              │
            ┌─────────────────┴──────────────────┐
            │  Almost all are useless:            │
            │   • not antimicrobial               │
            │   • or antimicrobial BUT hemolytic  │  ← the real trap
            │   • or active BUT already known     │  ← novelty/IP trap
            │   • or novel BUT unsynthesisable    │
            └─────────────────┬──────────────────┘
                              ▼
         We must find the vanishingly rare sequences that are
     ACTIVE  ∧  SELECTIVE  ∧  NOVEL  ∧  SYNTHESISABLE  ∧  IP-CLEAR
```

**Expert insight that shapes everything below:** the binding constraint is **not**
"is it an AMP" (predictors say yes easily) — it is **"will it spare host cells"**
(selectivity / low hemolysis). So the pipeline is deliberately weighted toward
selectivity and safety, and rejects the melittin-like high-hydrophobic-moment helices
that every naive generator over-produces.

---

## 2. End-to-End Pipeline (bird's-eye)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 0   KNOWLEDGE BASE          51,503 unique known AMPs (6 databases)        │
│           build_db() + build_kmer_index()                                       │
└───────────────┬──────────────────────────────────────────────────────────────┘
                │  (loaded once; reused by novelty scan AND motif prior-art)
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1   GENERATION              amphipathic helical-wheel construction (75%)  │
│           generate_expert_1000.py + pure-random diversity (25%)                  │
│           Hydrophobic residues placed on one helical face, cationic/polar on    │
│           the other (100°/residue wheel) → high μH by construction, not by luck;│
│           optional central Gly/Pro hinge inserted (selectivity motif).          │
└───────────────┬──────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2-5 run INSIDE each parallel worker (cost-ascending, reject cheap first): │
│                                                                                 │
│   2 cheap gates    charge, μH band, hydrophobic+aromatic caps, Trp≤2 (O(n))     │
│   3 k-mer novelty  no ≥3 consecutive known 5-mers (set lookups)                 │
│   4 MACREL GATE    calibrated ONNX models (independent): AMP-margin ≥ gold-      │
│       (the key)    standard panel AND Hemo-margin ≤ magainin. ~6% pass — the     │
│                    tightest gate, so run it BEFORE the expensive steps.          │
│   5a biophysics+QC selectivity≥0.55, safety≥0.55, activity≥0.50, synth≥0.70,    │
│                    no DKP/aspartimide/Trp-photolability                          │
│   5b NOVELTY SCAN  BLOSUM62 local identity vs all 51,503 AMPs; keep < 40%;       │
│                    any DRAMP-patent proximity rejected (CLEAR only)             │
└───────────────┬──────────────────────────────────────────────────────────────┘
                ▼  survival ≈ 1e-5 (Macrel-AMP ∩ novelty is intrinsically rare)
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 6   FINAL SCORE + DIVERSITY (main process)                                │
│   final = 0.55·expert_composite + 0.30·Macrel-AMP-like + 0.15·Macrel-NonHemo    │
│           (two independent model families must agree)                           │
│   diversity bucketing: ≤28 per (charge × length × hydrophobicity) bin           │
│           → ~850–896 ranked, scaffold-diverse candidates (see §3a)              │
└───────────────┬──────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 5   EXTERNAL VALIDATION (independent models we do NOT control)            │
│   local : Macrel (AMP + hemolysis)                                              │
│   web   : AMPScanner v2 · CAMPR4 · HemoFinder · AntiCP2                          │
│           strict shortlist = AMP+ ∧ NonHemo ∧ low-AntiCP ∧ predictor-consensus  │
└───────────────┬──────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 6   IP CLEARANCE (pre-filing)                                             │
│   BLASTp vs NCBI nr + pataa  ·  Lens.org / WIPO PatentScope exact-string        │
└───────────────┬──────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 7   WET-LAB PANEL          8–10 peptides → MIC + hemolysis + cytotoxicity │
│           the ONLY stage that can confirm discovery                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Why Cost-Ordering + Full Parallelism

Each gate has a different cost and a different rejection rate. Order them so the cheapest,
highest-rejection filters run first, and only the survivors pay for the expensive ones:

```
  per-candidate cost     reject rate   stage
  ───────────────────    ───────────   ─────────────────────────────
  O(n) counts   ~µs        ~87%        cheap biophysics prefilter
  set lookups   ~µs        small       k-mer prior-art
  ONNX 1 batch  ~30µs      ~94%        MACREL gate   ◄── tightest; run before features
  features+QC   ~ms        moderate    biophysical + synthesis QC
  BLOSUM×51503  ~10-100ms  high        novelty scan  ◄── most expensive; survivors only
```

**Two independent engineering wins:**

1. **Cost-ordering.** Running the ~94%-rejection Macrel gate (cheap ONNX) *before* the
   expensive `compute_features` + BLOSUM cut wasted feature computation ~16×.

2. **Full parallelism.** Each worker process self-generates candidates and runs the
   *entire* gauntlet locally; the main process only collects, dedups, diversity-caps,
   and applies the final composite. ONNX sessions are pinned to 1 thread/process to
   avoid core oversubscription. Result: ~7.75× scaling on 9 workers, ~240 MB peak RSS.

> Survival is ~1e-5 — not a bug. "Looks like an AMP to Macrel" ∩ "<40% identical to all
> 51,503 known AMPs" is genuinely rare, because real-AMP-like sequences resemble real
> AMPs. We pay for it with a large, fully-parallel search rather than by relaxing novelty.

## 3a. Why the batch is ~850–896, not exactly 1000 (diversity ceiling)

The final batch deliberately tops out **below** the nominal `--target 1000`. This is by
design, not a shortfall — it is the **scaffold-diversity ceiling**.

The diversity gate keeps at most `MAX_PER_BIN = 28` candidates per scaffold bin, where a
bin is `(charge bucket × length bucket × hydrophobicity bucket)`. Within the gate's own
acceptance window the number of *reachable* bins is small:

```
  charge bucket   min(charge,8)//2  over net charge +3..+8   →  ~4 values
  length bucket   len//4            over length 12..24        →  ~4 values
  hydrophob bucket int(hf*5)        over hf 0.30..0.50         →  ~2 values
                                                  ─────────────────────────
  reachable bins ≈ 4 × 4 × 2 = 32     →   hard ceiling ≈ 32 × 28 = 896
```

So **896 is the maximum a 28-per-bin cap can hold**, regardless of how long generation
runs. As the popular bins (e.g. charge +5, length 16–19, hf ≈ 0.4) saturate, the accept
rate falls (you can watch `/hr` drop in the checkpoints) and generation would otherwise
spin forever chasing the last, rarely-hit bins.

**Stall detection** ends the run gracefully: if no new candidate is accepted in
`STALL_LIMIT = 60,000,000` generated attempts, generation stops and keeps the full
diverse set reached (typically ~850–896). The `--target` is therefore an *upper cap*,
and the diversity cap + stall together set the *actual* count.

> **Why not just set `--target 896`?** Not every one of the 32 bins is equally reachable,
> so true saturation can land at ~870–890. Hard-coding 896 would risk stalling a few
> short and looking "unfinished." Leaving `--target 1000` lets the run take as many
> diverse candidates as the bins genuinely allow, then stop cleanly. The number you get
> *is* the diversity-limited maximum.
>
> **To get more than ~896:** raise `MAX_PER_BIN`, or make bins finer (e.g. use raw charge
> instead of `//2`, add an aromatic-fraction dimension). Both trade per-bin redundancy
> for total count — a deliberate diversity-vs-quantity choice, left as a config knob.

---

## 4. The Expert Composite (Stage 4 detail)

No single number captures a good candidate. A 30-year peptide chemist holds several
axes at once; `scoring/expert.py` makes that explicit and auditable.

```
expert_composite =
        0.22 · activity_consensus     physchem ∩ Boman, minus disagreement penalty
      + 0.22 · selectivity            charge/GRAVY therapeutic-window proxy
      + 0.18 · safety                 hemolysis-risk proxy (μH, hydrophobicity, charge)
      + 0.13 · synthesis              SPPS feasibility (length, repeats, aggregation)
      + 0.05 · serum_stability        proteolytic longevity (informational)
      + 0.08 · hinge_selectivity      central Gly/Pro hinge motif  ◄── NEW
      + 0.12 · motif_novelty          k-mer prior-art beyond global identity ◄── NEW
        ─────
         1.00   (weights fixed BEFORE ranking; deliberately tilted to selectivity+safety)
```

### 4a. Why two NEW signals that no prior module had

**Helix-hinge selectivity** — *"the expert sees a break at position N."*

```
   Rigid amphipathic helix              Hinged helix (Gly/Pro in centre)
   ───────────────────────              ────────────────────────────────
   ███████████████████████              ██████████▼██████████
   continuous hydrophobic face          two short faces, flexible kink
        │                                     │
        ▼                                     ▼
   efficient at lysing BOTH              still attracted to anionic
   bacterial AND zwitterionic            bacterial membranes, but a poor
   mammalian membranes → HEMOLYTIC       continuous pore-former in
                                         zwitterionic mammalian membranes
                                         → BETTER THERAPEUTIC WINDOW
```

A single helix-breaker (G/P) in the central third (cecropin-A's Gly23-Pro24 class)
scores 1.0; a continuous run of breakers shreds the helix and scores 0.1. A flat
hydrophobic-moment number is **blind to position** — this feature is not.
*Refs: Tossi et al. 2000 Biopolymers; Shai 2002 Biopolymers; Saberwal & Nagaraj 1994 BBA.*

**Motif-level prior art** — *"the expert recognises the local sequence."*

```
   Global BLOSUM identity: 38%   →  "looks novel"  ✔ passes the identity gate
                    BUT
   contains  ...R-W-W-K-G-G-W-Q...  a 7-mer copied verbatim from a known AMP
                    →  k-mer prior-art flags it as locally derivative  ✘
```

`build_kmer_index()` stores every 5-mer in the 51,503-sequence corpus; a candidate
sharing ≥3 *consecutive* known 5-mers is rejected. This is strictly sharper than a
global-identity threshold for catching "this looks like X."

### 4c. Calibrated Macrel in the loop (independent model, not just our own scores)

The strongest evidence is two *independent* model families agreeing. Macrel (Santos-Junior
et al. 2020) is an external trained AMP+hemolysis classifier. In this environment an
onnxruntime/ZipMap mismatch breaks its *absolute* probabilities (it mis-labels even
magainin-2). But the *relative* margin signal is intact and cleanly separates known AMPs
from non-AMPs:

```
   AMP margin:   gold-standard AMPs ▏──────[ −0.26 … −0.04 ]      (magainin, LL-37, …)
                 non-AMPs   ▏[ −1.00 … −0.51 ]──────              (polyK, insulin, albumin)
                                          ↑ clean separating gap ↑
                 gate = −0.30  →  "at least as AMP-like as the worst gold-standard AMP"
   Hemo margin:  melittin −0.01 (hemolytic)  >  magainin −0.09 (selective)
                 gate = −0.05  →  "no more hemolytic than magainin"
```

So every candidate is, by Macrel's own judgment, **as AMP-like as the gold-standard panel
and no more hemolytic than magainin** — recovered from a broken absolute output by
calibrating against known peptides. `final_score` blends this with the expert composite.

### 4b. The whole per-axis toolkit feeding the composite

```
   compute_features(seq) ─┬─► activity_likeness_score   (Zasloff, Hancock&Sahl)
                          ├─► boman_activity_score       (Boman 2003)  ← independent
                          ├─► model_disagreement         (uncertainty penalty)
                          ├─► safety_score               (Dathe&Wieprecht 1999; μH)
                          ├─► synthesis_feasibility      (SPPS rules)
                          ├─► serum_stability_score      (Hilpert 2006 protease sites)
                          ├─► selectivity_proxy          (Shai 2002 charge/GRAVY)
                          ├─► helix_hinge_analysis        ◄── NEW
                          └─► kmer_prior_art              ◄── NEW
   check_sequence(seq) ──► pre-synthesis QC: aspartimide(DG/DS), deamidation(NG/NS),
                           DKP(X-Pro), pyroglutamate(Q1), Trp-photolability(≥3W),
                           aggregation runs, C-amidation & N-acetylation guidance,
                           proline-rich intracellular-assay flag
```

---

## 5. Novelty & IP — defence in depth

```
  Layer 1  k-mer prior-art      local motif lifted from known AMP?      (generation)
  Layer 2  BLOSUM62 vs 51,503   global similarity < 40%?  patent-flagged? (generation)
  Layer 3  BLASTp NCBI nr+pataa  global vs ALL proteins + patent proteins (pre-filing)
  Layer 4  Lens.org / WIPO       exact-string in patent claims/listings   (pre-filing)
```

Thresholds (identity = matches / query length, BLOSUM62 local):

```
  ≥99%  EXACT_MATCH_OR_FRAGMENT     ┐
  ≥80%  KNOWN_VARIANT               │ excluded from novelty claims
  ≥60%  CLOSE_RELATIVE              ┘
  ≥40%  RELATED_NOVEL               ← allowed; note similarity in docs
  <40%  HIGH_CONFIDENCE_NOVEL       ← target
  patent DB hit at ANY identity ≥60% → POSSIBLE_PATENT_RISK → SYNTHESIS_HOLD
```

---

## 6. What each stage can and cannot claim

| Stage | Can claim | Cannot claim |
|-------|-----------|--------------|
| 1–2 Generation+gates | "biophysically AMP-plausible, synthesisable" | any activity |
| 3 Novelty | "<40% identity to 51,503 known AMPs; no patent proximity" | global IP clearance |
| 4 Expert composite | "ranks well on transparent multi-axis heuristic" | biological potency |
| 5 External predictors | "independent models concur it's AMP-like and low-hemolysis" | in-vitro activity |
| 6 IP clearance | "no exact prior art found in searched databases" | freedom-to-operate (needs counsel) |
| 7 Wet lab | **"experimentally validated"** | (this is the real result) |

> **The hard ceiling.** Every dry-lab improvement raises *confidence and efficiency*,
> not *proof*. The unlock is Stage 7. The pipeline exists to make Stage 7 cheap, fast,
> and aimed at the most defensible candidates — and to publish the negative results,
> benchmarks, and leakage checks regardless of outcome.

---

## 7. Data & Code Map

| Stage | Code | Output |
|-------|------|--------|
| 0 | `build_db()`, `build_kmer_index()` in `scripts/research/generate_expert_1000.py`; DBs in `data/novelty_db/` | in-memory corpus + 5-mer index |
| 1–4 | `scripts/research/generate_expert_1000.py` · `src/openamp_foundry/scoring/expert.py` | `outputs/expert_1000_candidates.{csv,fasta}` |
| 2c | `src/openamp_foundry/qc/presynth_check.py` | synthesis liability flags |
| 3 | `scripts/novelty/run_expanded_novelty_audit.py` | independent novelty re-audit |
| 5 | `scripts/research/screen_1000_candidates.py` (Macrel) + web predictors | `outputs/screening_1000/` |
| 6 | `scripts/novelty/run_patent_blastp.py` | `outputs/patent_blastp_*/ip_clearance_report.md` |
| 7 | `docs/review/WET_LAB_HANDOFF.md` | synthesis order + assay plan |

*See `docs/evidence/NOVELTY_AUDIT_GUIDE.md` for the canonical novelty methodology and database provenance.*
