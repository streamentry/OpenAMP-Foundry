# Citation and Reuse Guide

OpenAMP Foundry is an open research infrastructure project. This guide explains
how to cite the project and what you can reuse under which conditions.

## How to Cite

If you use OpenAMP Foundry in academic work, please cite:

**Inline citation:**
OpenAMP Foundry (Open-Problem-Lab, 2026), available at
https://github.com/Open-Problem-Lab/OpenAMP-Foundry

**BibTeX:**
```bibtex
@software{openamp_foundry_2026,
  author    = {{Open-Problem-Lab}},
  title     = {{OpenAMP Foundry: Verification-First Antimicrobial Peptide Discovery Infrastructure}},
  year      = {2026},
  url       = {https://github.com/Open-Problem-Lab/OpenAMP-Foundry},
  note      = {Dry-lab computational pipeline. Outputs are not biological proof.}
}
```

**Schema or artifact citation (add version):**
OpenAMP Foundry Artifact v0.7.x (Open-Problem-Lab, 2026).
Include the exact artifact version from `artifact_id` in the artifact manifest.

## What You Can Reuse

| Artifact type  | Reuse class           | License       | Attribution required |
|----------------|-----------------------|---------------|----------------------|
| Source code    | open                  | MIT           | Yes — preserve copyright notice |
| JSON schemas   | open                  | MIT           | Yes — preserve copyright notice |
| Documentation  | attribution_required  | CC-BY-4.0     | Yes — cite OpenAMP Foundry |
| Benchmark data | attribution_required  | CC-BY-4.0     | Yes — cite OpenAMP Foundry |
| Model weights  | contact_required      | CC-BY-NC-4.0  | Yes + contact maintainers |
| Candidate lists| restricted            | Proprietary   | Contact maintainers |

## Attribution Requirements

For **open** and **attribution_required** artifacts:
1. Include a clear reference to OpenAMP Foundry in your work.
2. Preserve the original copyright notice in any derivative files.
3. Do not imply endorsement by the OpenAMP Foundry team.
4. Retain the `dry_lab_only` label in any re-published computational outputs.

For **contact_required** artifacts:
1. Contact maintainers before use (see GOVERNANCE.md for contact information).
2. Attribution requirements as above apply.
3. Obtain written confirmation before publishing results derived from these artifacts.

For **restricted** artifacts:
1. Do not reuse without explicit written permission from maintainers.
2. Contact maintainers to discuss licensing terms.

## What NOT to Reuse Without Permission

- Candidate sequences in restricted status (pre-publication pipeline outputs)
- Lab synthesis orders or target prioritization lists
- Internal review committee deliberations
- Any artifact marked `release_status: restricted` in the artifact manifest

## Honest Use Boundary

Computational outputs from OpenAMP Foundry are **dry-lab candidates only**.
Do not describe them as "drugs," "proven antimicrobials," or "safe in humans."
Use language like: "computationally nominated candidates," "dry-lab selected sequences,"
"pending wet-lab validation."

## Machine-Validated Citation Entries

Citation entries can be validated with:
```bash
openamp-foundry citation-check --citation-json '{"artifact_id": "...", ...}'
```

See `src/openamp_foundry/governance/citation_policy.py` for the CitationEntry schema.

## Contact

For custom licensing, commercial use inquiries, or questions about reuse:
open an issue at https://github.com/Open-Problem-Lab/OpenAMP-Foundry/issues
with the label `governance`.

## Linked Policies

- [GOVERNANCE.md](../../GOVERNANCE.md) — project governance structure
- [DATA_LICENSE_NOTICE.md](../../DATA_LICENSE_NOTICE.md) — data licensing details
- [RESPONSIBLE_USE.md](../../RESPONSIBLE_USE.md) — responsible use policy
- [MODEL_RELEASE_POLICY.md](../../MODEL_RELEASE_POLICY.md) — model release policy
- [SECURITY_POLICY.md](SECURITY_POLICY.md) — vulnerability reporting
