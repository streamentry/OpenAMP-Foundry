# Data Source Documentation Guide

Every dataset used by the pipeline must be documented.

## Required Information
- Source URL or reference
- License information
- Download date
- Version or release
- Description of the data
- Known biases or limitations

## Format
Use a dataset card in `data/README.md` or in the relevant evidence document.

## Example
```markdown
## Dataset: Known AMPs (500)
- Source: UniProt reviewed + APD6 natural
- License: CC BY 4.0 (UniProt), academic use (APD6)
- Downloaded: 2026-07-01
- Description: 500 antimicrobial peptide sequences, 10-30 AA
- Known bias: Enriched for helical AMPs; fewer proline-rich and cysteine-rich
```
