# Citation Template for Data Consumers

This document provides copy-paste citation formats for teams and tools that use OpenAMP Foundry artifacts — evidence certificates, benchmark results, candidate packages, or pipeline outputs — in their own work.

Citing the specific artifact (not just the repository) is important because:

1. OpenAMP artifacts are versioned and may change across releases.
2. A citation that names the artifact ID and commit makes the evidence chain reproducible.
3. Reviewers can check the original dry-lab evidence without contacting the authors.

## What to cite

Cite **both** the repository and the specific artifact:

- **Repository**: cite the version or commit you used.
- **Artifact**: cite the artifact ID (e.g., `CERT-TOY-001`, `RMF-001`, `BCS-001`) and the release version or commit SHA where it appears in `outputs/`.

If the artifact was received in an external review packet, cite the packet ID (`ERP-`) as well.

## Citation formats

### Academic paper (APA-style)

```
OpenAMP Foundry Contributors. (2026). OpenAMP Foundry: Verification-first dry-lab
infrastructure for antimicrobial peptide candidate triage (v<VERSION>) [Software].
GitHub. https://github.com/Open-Problem-Lab/OpenAMP-Foundry
```

For a specific artifact:

```
OpenAMP Foundry Contributors. (2026). Evidence certificate <ARTIFACT_ID> from
OpenAMP Foundry v<VERSION> [Computational artifact]. Retrieved from
https://github.com/Open-Problem-Lab/OpenAMP-Foundry at commit <COMMIT_SHA>.
```

### BibTeX

```bibtex
@software{openamp_foundry,
  author       = {OpenAMP Foundry Contributors},
  title        = {{OpenAMP Foundry}: Verification-first dry-lab infrastructure
                  for antimicrobial peptide candidate triage},
  year         = 2026,
  publisher    = {GitHub},
  version      = {<VERSION>},
  url          = {https://github.com/Open-Problem-Lab/OpenAMP-Foundry},
  commit       = {<COMMIT_SHA>}
}
```

For a specific artifact:

```bibtex
@misc{openamp_artifact,
  author       = {OpenAMP Foundry Contributors},
  title        = {OpenAMP Evidence Artifact {<ARTIFACT_ID>}},
  year         = 2026,
  howpublished = {OpenAMP Foundry v<VERSION>, commit \texttt{<COMMIT_SHA>}},
  note         = {Computational dry-lab artifact. No biological activity implied.
                  Retrieved from \url{https://github.com/Open-Problem-Lab/OpenAMP-Foundry}.}
}
```

### CFF (Citation File Format)

The repository ships a `CITATION.cff` file at the root. Tools that read CFF (e.g., GitHub, Zenodo) will automatically extract this. If you need to override it for a specific artifact, create a local CFF:

```yaml
cff-version: 1.2.0
message: "If you use this artifact, please cite both the repository and the artifact ID."
title: "OpenAMP Foundry — Artifact <ARTIFACT_ID>"
version: "<VERSION>"
date-released: "<DATE>"
authors:
  - name: "OpenAMP Foundry Contributors"
repository-code: "https://github.com/Open-Problem-Lab/OpenAMP-Foundry"
commit: "<COMMIT_SHA>"
type: software
abstract: >
  Computational dry-lab artifact produced by OpenAMP Foundry.
  This artifact is a nominee from the dry-lab pipeline; no biological
  activity is implied. See the accompanying evidence certificate for
  the full provenance chain.
notes:
  - "Artifact ID: <ARTIFACT_ID>"
  - "Proof ladder level: dry_lab_candidate"
  - "Dry-lab only: true"
```

### Short in-text reference

For a brief in-text citation when a full reference is in the bibliography:

```
... selected using OpenAMP Foundry v<VERSION> (OpenAMP Foundry Contributors, 2026),
artifact ID <ARTIFACT_ID>, commit <COMMIT_SHA[:8]>.
```

### Data availability statement

When submitting a paper that uses OpenAMP outputs:

```
Data and code availability: Candidate evidence packages were generated using
OpenAMP Foundry v<VERSION> (https://github.com/Open-Problem-Lab/OpenAMP-Foundry,
commit <COMMIT_SHA>). All candidate IDs, evidence certificates, and benchmark
results are available at the repository under outputs/. Computational candidates
are computational nominees only; no biological activity or wet-lab validation
is implied by dry-lab certificate issuance.
```

## Placeholder reference

| Placeholder | Replace with |
|-------------|--------------|
| `<VERSION>` | The tagged release, e.g. `v0.8.0` |
| `<COMMIT_SHA>` | The full git commit SHA, e.g. `3c56621...` |
| `<COMMIT_SHA[:8]>` | First 8 characters of the commit SHA |
| `<ARTIFACT_ID>` | The artifact's machine-readable ID, e.g. `CERT-TOY-001` |
| `<DATE>` | ISO 8601 date of the artifact, e.g. `2026-01-01` |

## What NOT to cite as evidence of biological activity

OpenAMP artifacts are computational dry-lab outputs. Do not cite them as:

- Evidence of antimicrobial activity.
- Proof of safety, non-toxicity, or hemolysis resistance.
- A substitute for peer-reviewed wet-lab validation.
- A basis for any therapeutic or clinical claim.

A proper citation should be accompanied by a statement that the artifact is a computational nominee, not a validated compound.
