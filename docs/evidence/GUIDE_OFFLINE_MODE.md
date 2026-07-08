# Offline Mode Explanation

OpenAMP Foundry tools are designed to work offline by default.

## What Works Offline
- All local checks: `check_doc_links.py`, `check_claims.py`, `check_pyproject.py`
- Lab result validation: `validate_lab_data_return.py`, `check_wave1_pass_fail.py`
- Negative archive validation: `validate_negative_archive.py`
- Panel CSV validation: `validate_panel_csv.py`
- Benchmark calculations
- All tests (after initial `pip install`)

## What Requires Network
- Initial `pip install`
- Downloading reference databases for novelty checks
- External predictor submissions
- Novelty database refresh

## Why Offline Matters
- Reproducibility — results should not depend on network availability
- Security — no data leakage through network calls
- Speed — local checks are faster than network-dependent ones
