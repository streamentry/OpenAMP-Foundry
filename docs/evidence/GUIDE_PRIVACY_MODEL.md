# Privacy Model Overview

How OpenAMP Foundry handles privacy and data.

## Data Collected
- Candidate sequences (provided by the user)
- Lab result data (provided by the user)
- Pipeline output files (stored locally)

## Data NOT Collected
- No telemetry
- No analytics
- No usage statistics
- No personal information

## Data Sharing
- Adapters do not send data without explicit user consent.
- External predictors require user-initiated submission.
- No data is shared with third parties without user action.

## Local-Only Guarantee
All core pipeline operations run locally. No data leaves your machine
unless you explicitly use an external adapter or predictor.
