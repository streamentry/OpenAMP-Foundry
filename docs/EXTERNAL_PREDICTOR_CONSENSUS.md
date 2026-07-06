# External Predictor Consensus

## Purpose

Aggregate predictions from 5 independent AMP prediction tools into a single
consensus verdict per candidate. A candidate with ≥3/5 tool agreement is
classified as **CONFIDENT** and recommended for synthesis.

## Tool Summary

| Tool | Method | Positive label | URL |
|------|--------|---------------|-----|
| CAMPR4 | SVM + RF + ANN + DT ensemble | AMP | camp3.bicnirrh.res.in |
| AMPScanner v2 | LSTM | Antimicrobial | dveltri.com/ascan/v2 |
| dbAMP 2.0 | Random Forest | AMP | awi.cuhk.edu.cn/dbAMP |
| AntiCP 2.0 | SVM | ACP (not AMP) | webs.iiitd.edu.in/raghava/anticp2 |
| Macrel | Random Forest | AMP | big-data-biology.org/software/macrel |

## Consensus Rules

| Agreement | Verdict | Action |
|:---------:|---------|--------|
| ≥3/5 | CONFIDENT | Proceed to synthesis |
| 2/5 | UNCERTAIN | Expert review required |
| ≤1/5 | WEAK | Do not synthesise |

## Current Status

This document describes the **generic pilot-panel consensus workflow**. It remains
unresolved for any future panel until that panel has a filled
`outputs/external_predict_results.csv` and a generated consensus report.

Current Wave 0.5 status is different: the completed Wave 0.5 screen is summarized in
`docs/evidence/METRICS_CURRENT.md`. CAMPR4 was not submitted, so Wave 0.5 activity consensus is
based on three activity predictors (AMPScanner v2, AMPActiPred, Macrel web server) plus
separate HemoFinder and AntiCP 2.0 safety annotations. Do not treat this generic 5-tool
template as evidence that Wave 0.5 remains wholly pending.

Macrel v1.6.0 CLI has a known ONNX bug (all candidates classified NAMP — see PR #77);
use the web server at `big-data-biology.org/software/macrel` instead.

### How to Fill

1. Submit `outputs/pilot_panel.fasta` to each tool's web interface
2. Record Y/N per candidate in `outputs/external_predict_results.csv`
3. Run: `make external-consensus RESULTS=outputs/external_predict_results.csv`
4. Gate 6 (`gate-check --gate 6`) will then pass/fail for real

### Tool URLs

| Tool | URL |
|------|-----|
| CAMPR4 | http://www.camp3.bicnirrh.res.in/predict.php |
| AMPScanner v2 | https://www.dveltri.com/ascan/v2/ascan.html |
| dbAMP 2.0 | https://awi.cuhk.edu.cn/dbAMP/predict.php |
| AntiCP 2.0 | https://webs.iiitd.edu.in/raghava/anticp2/ |
| Macrel | https://big-data-biology.org/software/macrel (web server) |

## CLI Usage

```bash
# After filling in results CSV:
make external-consensus RESULTS=outputs/external_predict_results.csv

# Or manually:
openamp-foundry external-consensus \
    --pilot-csv outputs/pilot_panel.csv \
    --results-csv outputs/external_predict_results.csv \
    --out outputs/external_consensus_report.md
```

## See Also

- `outputs/external_predict_checklist.md` — Manual submission guide
- `src/openamp_foundry/reports/external_consensus.py` — Implementation
- `docs/review/ASSAY_PREREGISTRATION.md` — Pre-registered assay protocol
