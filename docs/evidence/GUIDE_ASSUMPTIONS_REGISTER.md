# Assumptions Register Guide

How to document and track assumptions.

## What to Record
- Assumptions about data quality
- Assumptions about model behavior
- Assumptions about benchmark validity
- Assumptions about user environment

## Format
Each assumption should include:
- What the assumption is
- Why it's reasonable
- What would happen if it's wrong
- When it should be reviewed

## Example
| Assumption | Basis | Risk if Wrong | Review Date |
|-----------|-------|---------------|-------------|
| AMPs are cationic | Literature consensus | Non-cationic AMPs undervalued | Next benchmark cycle |
| Swiss-Prot decoys are valid negatives | Standard practice | Benchmark AUROC inflated | Next data refresh |
