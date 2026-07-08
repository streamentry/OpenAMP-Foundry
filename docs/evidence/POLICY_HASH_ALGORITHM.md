# Hash Algorithm Policy

Hash algorithms used in the pipeline.

## Current Algorithms
| Algorithm | Used For | Strength |
|-----------|----------|:--------:|
| SHA-256 | Evidence certificates, manifests, chain of custody | Strong |
| SHA-256 | Input file hashing for reproducibility | Strong |

## Requirements
- All hashes must use SHA-256 or stronger.
- MD5 and SHA-1 are forbidden for security-sensitive uses.
- Hash algorithms must be documented in the relevant schema.
- Hash values must be hex-encoded, lowercase.

## Verification
- Hash verification is built into chain-of-custody scripts.
- Run `scripts/verify_lab_peptides.py` to verify sequence hashes.
- Manifests include hashes for all input files.
