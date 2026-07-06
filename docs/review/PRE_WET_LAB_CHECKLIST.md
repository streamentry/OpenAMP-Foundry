# Pre-Wet-Lab Submission Checklist

> **Purpose:** One-page guide to everything that must be done before submitting
> the 20-candidate pilot panel to a synthesis vendor and wet-lab.
>
> **Current status:** 53/100 breakthrough potential.
> After completing this checklist: 55–65/100.
>
> **Estimated time:** Historical estimate for the original manual-submission pass.
> The external predictor portion has since been completed; remaining blockers are novelty/legal/expert review and wet-lab execution.

---

## Quick Start

```text
1. Review current external predictor evidence   (done historically; see current-state docs)
2. Confirm full novelty / FTO posture           (~30-90 min depending on scope)
3. Invite expert reviewer                       (~1 week)
4. Lock pre-registration                        (~10 min)
5. Order synthesis                              (vendor lead time)
```

---

## Step 1 — External Predictor Consensus

Submit `outputs/pilot_panel.fasta` to each tool below.
Record Y (predicted AMP) or N (not AMP) for each candidate.

### Tool 1: CAMPR4

| Field | Value |
|-------|-------|
| URL | https://camp3.bicnirrh.res.in/predict/ |
| Method | SVM + Random Forest + ANN + Decision Tree (ensemble vote) |
| Submission | Paste FASTA in text box, select all four models, submit |
| Export | CSV results (there should be a download link) |
| Label | Positive = **AMP** |
| Tip | Use the 'Predict' tab, not the sequence database |

**Per-candidate rule:** CAMPR4 uses 4 models with majority vote. Record Y if ≥3/4 models vote AMP.

### Tool 2: AMPScanner v2.0

| Field | Value |
|-------|-------|
| URL | https://www.dveltri.com/ascan/v2/ascan.html |
| Method | LSTM deep learning trained on APD + UniProt |
| Submission | Paste FASTA or upload file, click 'Predict' |
| Label | Positive = **Antimicrobial** |
| Tip | Records probability score. Use threshold ≥ 0.5 for binary call |

**Per-candidate rule:** Record Y if probability ≥ 0.5.

### Tool 3: dbAMP 2.0

| Field | Value |
|-------|-------|
| URL | https://ycclab.cuhk.edu.cn/dbAMP/analyze.php |
| Method | Random Forest on physicochemical + AA composition |
| Submission | Paste FASTA, click 'Predict' |
| Label | Positive = **AMP** |
| Tip | Also reports predicted activity spectrum (antibacterial/antifungal) |


https://ycclab.cuhk.edu.cn/dbAMP/HemoFinder_result.php?ID=HVM0vChd_
https://ycclab.cuhk.edu.cn/AMPActiPred/
https://ycclab.cuhk.edu.cn/AMPActiPred/result.php?ID=aCdkKYcv_OpenAMPWave1
Step 2: Predict functional type? → Yes
Step 3: Select type → tick ALL bacteria
Step 4: Predict activity levels? → Yes
Step 5: Project name → OpenAMPWave1


Minimum must-tick set:

E. coli
S. aureus
P. aeruginosa
A. baumannii
K. pneumoniae
E. faecalis
S. typhimurium

Also tick these if allowed:

B. subtilis
S. epidermidis
M. luteus

**Per-candidate rule:** Record Y if predicted as AMP.

### Tool 4: AntiCP 2.0

| Field | Value |
|-------|-------|
| URL | https://webs.iiitd.edu.in/raghava/anticp2/predict.php |
| Method | SVM trained on anticancer peptides |
| Submission | Select 'Predict' tab, paste sequences one per line (NOT FASTA format) |
| Label | Positive = **ACP** (anticancer peptide — NOT AMP-specific) |
| Caution | AntiCP predicts ACP, not AMP. ACP and AMP activity correlate but are not identical. Count ACP-positive as **indirect supporting evidence only**. |

**Per-candidate rule:** Record Y if predicted as ACP. Mark as caveat in the consensus report.

Tick Model 1, keep SVM threshold = 0.45, upload pilot_panel.fasta.

Do not use Hybrid_DS1 / Hybrid_DS2 for the full batch, because your panel has many peptides under 15 AA. The page itself says the hybrid/N15C15 model needs at least 15 residues, and many of your candidates are 11–14 AA.

For the physicochemical properties, they usually only affect displayed descriptors, not the classifier. Tick:

Hydrophobicity
Hydropathicity
Hydrophilicity
Charge
Amphipathicity
Molecular weight
pI

Net Hydrogen / Steric hindrance / Side bulk are optional. They are not critical for your Gate 6 consensus.


### Tool 5: Macrel (web server ONLY)

| Field | Value |
|-------|-------|
| URL | https://big-data-biology.org/software/macrel |
| Method | Random Forest on 22 physicochemical + 8 structural features |
| Submission | Use the **web server** (NOT the local CLI — has a known ONNX bug, PR #77) |
| Label | Positive = **AMP** (`is_AMP = True`) |
| Tip | Also reports hemolytic probability — useful cross-check |

**Critical:** The local CLI (`pip install macrel`) has a known ONNX bug where all sequences
(including canonical AMPs like magainin-2 and LL-37) are classified as NAMP. Always use the
web server at `https://big-data-biology.org/software/macrel`.

**Per-candidate rule:** Record Y if `is_AMP = True`. Record hemolysis risk separately.

### Recording Results

After submitting to all 5 tools, fill in the results CSV:

```bash
# Template already exists at:
outputs/external_predict_results.csv

# Fill Y or N for each candidate in each tool column:
#   candidate_id,CAMPR4,AMPScanner,dbAMP,AntiCP2,Macrel
#   SEED-009_VAR_033,Y,N,Y,N,Y

# Then generate the consensus report:
make external-consensus RESULTS=outputs/external_predict_results.csv

# Or manually:
openamp-foundry external-consensus \
    --pilot-csv outputs/pilot_panel.csv \
    --results-csv outputs/external_predict_results.csv \
    --out outputs/external_consensus_report.md
```

### Expected Outcome

| Consensus | Candidates | Action |
|-----------|:----------:|--------|
| **CONFIDENT** (≥3/5 tools Y) | ≥12 | Proceed to synthesis |
| **UNCERTAIN** (2/5 tools Y) | 6–11 | Expert review required |
| **WEAK** (≤1/5 tools Y) | <6 | Do NOT proceed; re-evaluate pipeline |

---

## Step 2 — Novelty Gate (Full-DB Audit Required Before Panel Lock)

> **⚠ Postmortem gate (2026-06-29):** A preliminary 72-sequence novelty check returned
> NOVEL for SEED-020_VAR_004/002 while the full BLOSUM62 audit (27,234 sequences, patent DB
> included) classified them CLOSE_RELATIVE / POSSIBLE_PATENT_RISK. **Always use the full
> audit tool before adding any candidate to `wave1_final_panel.csv` or citing a novelty
> status in a submission document.** See `docs/postmortems/2026-06-29-seed020-novelty-patent-risk.md`.

### Gate: Full BLOSUM62 audit must exist for every panel candidate

Before adding a candidate to `outputs/wave1_final_panel.csv`:

```bash
# Verify the candidate appears in the full audit output:
grep "CANDIDATE_ID" outputs/wave0_5_novelty_audit_v2.csv

# If missing, run the full audit (includes 27,234 sequences, DRAMP patent sub-DB):
python scripts/run_wave0_5_novelty_audit_v2.py
```

**Do NOT cite the `novelty-check-broad` CLI result alone in any submission document.**
That tool uses a 72-sequence database with no patent sequences — it is a fast preliminary
filter only, not a sufficient novelty gate.

### Scaffold continuity rule

If any existing variant of a seed family is classified POSSIBLE_PATENT_RISK in the full
audit, **all new variants from that family must also be run through the full audit before
documentation**, regardless of preliminary check results.

### The internal 120-sequence novelty audit is a preliminary screen.
Before publication, verify against the full public databases.

### Database BLAST

| Database | URL | What to check |
|----------|-----|---------------|
| **APD3** | https://aps.unmc.edu/AP/ | > 3,000 natural AMPs — check each candidate |{checklist_item}|
| **DRAMP v3.0** | http://dramp.cpu-bioinfor.org/ | > 19,000 entries including synthetic AMPs |
| **dbAMP 2.0** | https://awi.cuhk.edu.cn/dbAMP/ | > 4,000 validated AMPs with activity spectra |
| **CAMPR4 DB** | http://www.camp3.bicnirrh.res.in/ | Collection of sequences + structures |
| **NCBI BLASTp** | https://blast.ncbi.nlm.nih.gov/ | UniProtKB/Swiss-Prot + patent sequences |
| **LENS.org** | https://www.lens.org/ | Patent sequence search |

### Rule

```text
Identity ≥ 80% to any known sequence → KNOWN_VARIANT (not novelty-claimable)
Identity 50–80% → CLOSE_RELATIVE (conditional)
Identity < 50% → NOVEL (claimable)
```

### Quick Check

For the most important candidates (SEED-006, 007, 008, 009), run the 8-AA motif search:

```text
SEED-006: INWKPIAAMAKKLV  → search "INWKPIA" in each database
SEED-007: IKFTTMLRKLG     → search "IKFTTML" in each database
SEED-008: FPVTWRFWRWWKG   → search "FPVTWRF" in each database
SEED-009: RRLPRPGYMPRP    → search "RRLPRPG" in each database
```

If none of these motifs have exact database matches, the novelty claim is strong.

See `docs/NOVELTY_CHECKLIST.md` for the full step-by-step guide.

---

## Step 3 — Expert Reviewer Invitation

### Who to Ask

An expert reviewer should be a qualified microbiologist, peptide chemist, or
infectious disease specialist — ideally someone who:
- Has published AMP research
- Has experience with MIC/hemolysis assays
- Is independent (not a collaborator or co-author)

### What to Send

| Document | Purpose |
|----------|---------|
| `docs/REVIEWER_SUMMARY.md` | 2-page quick overview — start here |
| `docs/EXPERT_REVIEW_PACK.md` | Full expert review packet with all candidate data |
| `docs/NOVELTY_AUDIT_FULL.md` | Novelty classification against 120-AMP library |
| `docs/BENCHMARK_CARD.md` | Benchmark methodology and metrics |
| Generated questionnaires | `make questionnaire` → `outputs/questionnaire/*.md` |

### Reviewer Questionnaire

Generate pre-populated questionnaires for each candidate:

```bash
make questionnaire
# Creates outputs/questionnaire/SEED-*.md — one per candidate
```

Each questionnaire asks:

```text
1. Any obvious synthesis issues?
2. Any motifs of concern?
3. Do you agree with the novelty classification?
4. Hemolysis risk acceptable?
5. Cytotoxicity flags addressed?
6. Overall: APPROVE / CONDITIONAL / REJECT
```

Collect the signed questionnaires and store them before synthesis ordering.

### After Review

```bash
# Check if expert review gate passes (will show PENDING until questionnaires returned):
openamp-foundry gate-check --gate 7
```

---

## Step 4 — Final Decision Gates

After external predictors and expert review are complete, verify all gates:

```bash
# Check all gates at once:
make gate-check

# Expected output for a synthesis-ready pipeline:
# Gate 1 (AUROC)         → PASS (0.7832 ≥ 0.70)
# Gate 2 (Leakage)       → PASS
# Gate 3 (Disagreement)  → PASS
# Gate 4 (Recall@10)     → PASS
# Gate 5 (Interpretation)→ PASS (STRONG)
# Gate 6 (Ext. consensus)→ PASS (≥3/5 tools agree)
# Gate 7 (Expert review) → PASS (reviewer APPROVE)
# all_pass: true
```

---

## Step 5 — Synthesis Order

```bash
# Generate vendor-ready order:
make synthesis-order
# Creates outputs/synthesis_order.csv (GenScript-compatible)
# Creates outputs/synthesis_checklist.md

# Then order from a qualified peptide synthesis vendor:
# - GenScript (standard)
# - Peptide 2.0 (standard)
# - Bachem (premium)
# - CPC Scientific (premium)
```

---

## Step 6 — Lock Pre-Registration

1. Fill in PI signature in `docs/ASSAY_PREREGISTRATION.md` §9
2. Commit the filled document to the repo (locked before wet-lab data)
3. Share the assay protocol with the wet-lab team

The pre-registration covers:
- MIC protocol (EUCAST ISO 20776-1)
- Hemolysis protocol (hRBC, 1–512 µg/mL)
- Serum stability protocol (50% human serum, 0/30/60/120 min)
- Hit definition (MIC ≤ 32 µg/mL AND TI > 10)
- Statistical plan (biological triplicate, geometric mean)

---

## Quick Reference — All Commands

```bash
# 1. External predictor consensus
make external-consensus RESULTS=outputs/external_predict_results.csv

# 2. Generate reviewer questionnaires
make questionnaire

# 3. Check all gates
make gate-check

# 4. Generate synthesis order
make synthesis-order

# 5. Run tests (should be 1343 passing)
make test

# 6. Check lint
make lint
```

---

## Summary of What Changes After Each Step

| Step | Score | Gate 6 | Gate 7 | Synthesis ready? |
|------|:-----:|:------:|:------:|:----------------:|
| Historical baseline before external predictor completion | 53 | PENDING | PENDING | ❌ |
| After external predictor completion | 56–58 | PASS/FAIL | PENDING | ❌ |
| After Step 3 (expert review) | 60–65 | PASS/FAIL | PASS | ⚠️ conditional |
| After Steps 4–6 (all gates pass) | 65–70 | PASS | PASS | ✅ |

---

*Generated by OpenAMP Foundry. See individual docs/ files for details.*
