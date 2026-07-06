# Agent Prompt — External Validation of OpenAMP Candidates (Playwright)

> **This is implemented and working.** Raw HTTP (`curl`) does NOT work for these tools —
> they render results via client-side JavaScript + server sessions, so a **real browser
> via Playwright** is required. Working drivers live in `scripts/external_validators/`.
>
> **Context:** these are de-novo antimicrobial peptide (AMP) candidates from a
> reproducible, safety-first discovery pipeline. The goal is purely defensive — find
> peptides that may inhibit drug-resistant bacteria with low mammalian toxicity.
> Legitimate scientific validation; no dual-use concern.

## How to run (proven, 2026-06-30)

```bash
# The CLI natively automates Playwright to submit candidates and parse results:
openamp_foundry external-predict --pilot-csv outputs/wave1_final_panel.csv
```
The CLI command automatically:
1. Generates the required FASTA file.
2. Checks for and installs Node.js/Playwright dependencies in `scripts/external_validators`.
3. Runs the 4 headless Playwright predictors sequentially (AMPScanner, AntiCP2, CAMP-R4, HemoFinder).
4. Drops results into `outputs/external_validation/`.
5. Prompts you to run `openamp_foundry external-consensus` to compile the final cross-tool consensus matrix.


### Proven Playwright patterns (per tool)

| Tool | Form field(s) | Submit | Result handling |
|------|---------------|--------|-----------------|
| AntiCP2 | `textarea[name=seq]` | `input[type=submit][value=Submit]` | navigates to `disp.php`; parse `<table>` rows (ID, Seq, Score, Prediction) |
| CAMP-R4 | `textarea[name=S1]` + check `input[name="algo[]"][value=svm/rf/ann/da]` | `input[name=B1]` | `hii.php`; 4 classifier tables, rows = (index, class, prob), map index→ID by input order; wait ~8–60 s |
| AMPScanner v2 | `input[name=seqInputFile]` (file upload) | `input[type=submit]` | inline table; row = (`ID\nSEQ`, class, prob); prob>0.5 = AMP |
| HemoFinder | `input[name=SEQFILE]` upload or `textarea[name=SEQTEXT]` | `#startfinder` | **async** → `HemoFinder_result.php?ID=…`; POLL up to ~150 s until `Low/High-hemolysis` appears |
| AMPActiPred | same as HemoFinder (`SEQTEXT`/`SEQFILE`, `#startfinder`) | | **async + slow**; often >240 s — retry off-peak |

Key gotchas baked into the drivers: CUHK servers (HemoFinder/AMPActiPred) need
`waitUntil:'domcontentloaded'` + 120 s nav timeout + result polling; guard
`document.body` reads against null during navigation; chunk large batches
(CAMP 100, AntiCP2/HemoFinder 100–150) to avoid timeouts.

---

## (Reference) Original tool list and consensus spec

---

## 0. Inputs and outputs

**Input FASTA files** (in the repo; the count is ~450, the `1000`/`all_1000` names are
historical — submit whichever the tool's batch limit allows):

| File | Count | Use |
|------|-------|-----|
| `outputs/external_submission/all_1000.fasta` | ~450 | tools with no/large upload cap |
| `outputs/external_submission/top200.fasta` | 200 | tools capped at a few hundred |
| `outputs/external_submission/top50_strict.fasta` | ~21 | priority shortlist, always submit |

Each header already carries our internal scores, e.g.:
`>XPRT_0007 final=0.699 macrel_amp=0.71 nonhemo=0.10 expert=0.79 sim=37.5% charge=4.5 hinge=1`

**Save all results under** `outputs/external_validation/` using the exact filenames given
per tool below. Create the directory if missing.

**Operating rules**
- Respect each tool's batch limit; if the full set exceeds it, split into chunks
  (e.g. 100/submission), submit sequentially, and concatenate the result tables.
- If a site shows a CAPTCHA, email gate, or login wall, STOP for that tool, record
  `BLOCKED: <reason>` in `outputs/external_validation/run_log.md`, and continue with the
  rest. Do not attempt to bypass access controls.
- Capture the **raw** result table (download CSV/TSV if offered; otherwise scrape the
  results HTML table) AND a screenshot of the results page for provenance.
- Record submission settings (model/threshold chosen) in `run_log.md`.
- Never edit the input sequences. Keep candidate IDs (`XPRT_####`) as the join key.

---

## 1. The seven predictors

For each: open the URL, locate the sequence input (file upload or textarea), submit the
FASTA, wait for completion, and save results to the named file.

### 1.1 CAMP-R4 — AMP probability (4 algorithms)
- URL: https://camp3.bicnirrh.res.in/predict/
- Submit FASTA. Select **all** prediction models offered (SVM, RF, ANN, DA).
- Capture per-sequence prediction + probability for each algorithm.
- Save → `camp4_results.csv` (columns: candidate_id, camp_svm, camp_rf, camp_ann, camp_da, camp_call).

### 1.2 AMP Scanner v2 — deep-learning AMP classifier
- URL: https://www.dveltri.com/ascan/v2/ascan.html
- Upload FASTA. Use the default trained model.
- Capture per-sequence AMP/non-AMP call + prediction score (probability).
- Save → `ampscanner_results.csv` (candidate_id, ampscanner_call, ampscanner_score).

### 1.3 AMPActiPred — antibacterial activity prediction
- URL: https://ycclab.cuhk.edu.cn/AMPActiPred/
- Submit FASTA. Capture the ABP (antibacterial peptide) call and any activity/potency tier.
- Save → `ampactipred_results.csv` (candidate_id, abp_call, activity_tier_or_score).

### 1.4 HemoFinder (dbAMP) — hemolysis risk
- URL: https://ycclab.cuhk.edu.cn/dbAMP/HemoFinder.php
- Submit FASTA. Capture hemolytic / non-hemolytic call + score.
- Save → `hemofinder_results.csv` (candidate_id, hemo_call, hemo_score).

### 1.5 dbAMP community prediction
- URL: https://ycclab.cuhk.edu.cn/dbAMP/community.php
- Submit FASTA. Capture whatever AMP / functional-activity call the tool returns.
- Save → `dbamp_community_results.csv` (candidate_id, dbamp_call, dbamp_score_or_fields).

### 1.6 AntiCP2 — off-target (anticancer) signal
- URL: https://webs.iiitd.edu.in/raghava/anticp2/predict.php
- Submit FASTA (model 1, default threshold 0.5). We WANT **Non-AntiCP** (low off-target).
- Capture AntiCP / Non-AntiCP call + score.
- Save → `anticp2_results.csv` (candidate_id, anticp_call, anticp_score).

### 1.7 Macrel (web) — AMP + hemolysis
- URL: https://www.big-data-biology.org/software/macrel/
- Use the web server / Galaxy entry point. Submit FASTA (peptides mode).
- Capture is_AMP + AMP_probability and Hemolytic + Hemo_probability.
- Save → `macrel_web_results.csv` (candidate_id, macrel_amp, macrel_amp_prob, macrel_hemo, macrel_hemo_prob).
- NOTE: our local Macrel had an onnxruntime calibration bug; the **web** Macrel is the
  trusted reference — record its absolute probabilities.

---

## 2. Normalise each result table

For every `*_results.csv`, coerce to a common per-tool verdict so they can be intersected.
Add two boolean columns where the tool provides the signal:

- `is_amp_positive` — tool calls it an AMP / antibacterial (CAMP, AMPScanner, AMPActiPred,
  dbAMP, Macrel-web).
- `is_nonhemolytic` — tool calls it non-hemolytic (HemoFinder, Macrel-web).
- `is_non_anticp` — AntiCP2 says Non-AntiCP (off-target clear).

Keep the raw scores too. Join all tables on `candidate_id` into one wide matrix:
`outputs/external_validation/consensus_matrix.csv`.

---

## 3. Consensus analysis

Produce `outputs/external_validation/consensus_report.md` containing:

1. **Per-tool summary** — for each predictor: N submitted, N AMP-positive, N
   non-hemolytic, N blocked/failed, and the submission settings used.

2. **Cross-tool agreement table** — for each candidate, the count of independent AMP-
   positive calls (out of the AMP-predicting tools) and the hemolysis verdicts.

3. **Strict consensus shortlist** — candidates that are **AMP-positive on ≥3 independent
   tools AND non-hemolytic on HemoFinder AND Macrel-web AND Non-AntiCP on AntiCP2**.
   Rank this shortlist by (number of AMP-positive calls, then our internal `final_score`
   from the FASTA header). This is the wet-lab priority set.

4. **Disagreement flags** — candidates where tools strongly disagree (e.g. high internal
   `final_score` but AMP-negative on most external tools, or non-hemolytic internally but
   hemolytic on HemoFinder). These need a skeptical look.

5. **Headline numbers** — "X / 450 are AMP-positive on ≥3 tools; Y are strict-consensus
   clean; top candidate is XPRT_#### with N/7 tool support."

Also write `outputs/external_validation/strict_consensus_shortlist.csv` (the ranked set
from step 3) and `outputs/external_validation/strict_consensus_shortlist.fasta`.

---

## 4. Deliverables checklist

```
outputs/external_validation/
  run_log.md                         # per-tool: settings, blocks, timestamps
  camp4_results.csv
  ampscanner_results.csv
  ampactipred_results.csv
  hemofinder_results.csv
  dbamp_community_results.csv
  anticp2_results.csv
  macrel_web_results.csv
  screenshots/<tool>.png             # provenance for each results page
  consensus_matrix.csv               # all tools joined on candidate_id
  consensus_report.md                # the analysis (section 3)
  strict_consensus_shortlist.csv     # ranked wet-lab priority set
  strict_consensus_shortlist.fasta
```

**Success criterion:** every reachable tool has a saved result table and a screenshot, the
consensus matrix joins them all on `candidate_id`, and the report names a ranked
strict-consensus shortlist with explicit tool-support counts. Report any tool that was
blocked and why, rather than guessing or fabricating its output.
```
