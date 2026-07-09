# Public-Good Contribution Guide

## Purpose

OpenAMP Foundry is an open-source, dry-lab infrastructure for antimicrobial
peptide candidate selection. Its mission is to make candidate selection more
reproducible, safer to audit, and harder to fool.

**Public-good contributions** are contributions that advance this mission
without proprietary gatekeeping, private benefit, or biological harm. They
are reviewed, attributed, and released under open terms so that the whole
research community benefits.

Institutional contributions are how universities, research hospitals,
nonprofits, government labs, and open-source bioinformatics projects turn
computational outputs into shared evidence. This guide tells you how.

---

## Who can contribute

- **Universities** and academic research groups
- **Research hospitals** and clinical research organisations
- **Nonprofit** research institutes and foundations
- **Government laboratories** and public-health agencies
- **Open-source bioinformatics projects** publishing under OSI-approved
  licenses

Commercial entities are welcome to contribute through other channels
(see [GOVERNANCE.md](../../GOVERNANCE.md)). This guide is scoped to
public-good institutional contributors.

---

## Contribution types

| Type | What it is | Minimum requirements | Review class |
|------|-----------|---------------------|-------------|
| `wet_lab_validation` | Experimental MIC / hemolysis data for nominated dry-lab candidates | institution_name, contact_email, candidate_ids, assay_type, data_license | D (human review mandatory) |
| `dataset_donation` | Curated AMP or non-AMP datasets with full provenance | institution_name, contact_email, dataset_description, data_license, record_count | B |
| `compute_sponsorship` | HPC time or GPU credits for simulation runs | institution_name, contact_email, compute_hours, platform | B |
| `expert_review` | Structured peer review of evidence packets | institution_name, contact_email, reviewer_expertise, scope | D (human review recommended) |
| `governance_participation` | Serving on advisory or review panels | institution_name, contact_email, role, availability | A |
| `algorithm_contribution` | New scoring or simulation modules with tests | institution_name, contact_email, algorithm_description, has_tests, data_license | B |

### Review classes

- **A** — Low risk. Governance roles and administrative contributions.
  Fast-track review.
- **B** — Moderate risk. Datasets, algorithms, and compute sponsorships
  require verification of claims, licensing, and reproducibility.
- **C** — Reserved for future use.
- **D** — High risk. Wet-lab validation and expert review require
  mandatory human review before acceptance into the pipeline.

---

## How to initiate

1. **Open a GitHub issue** at
   [github.com/anomalyco/openamp-foundry/issues](https://github.com/anomalyco/openamp-foundry/issues).
2. **Apply the label** `institutional-contribution`.
3. **Include:**
   - Institution name
   - Contact email
   - Contribution type (from the table above)
   - Proposed scope (what you want to do or provide)
   - Any relevant links (preprints, repositories, data sources)

You can use the `openamp-foundry contribution-check` CLI to validate your
intake before submitting:

```bash
openamp-foundry contribution-check \
  --intake-json '{"institution_name":"Example University","contact_email":"research@example.edu","contribution_type":"dataset_donation","proposed_scope":"Curated AMP dataset 500 sequences","human_review_required":false,"dry_lab_only":true,"data_license":"CC-BY-4.0","dataset_description":"AMP sequences with MIC data","record_count":500}'
```

---

## What to expect

### Review timeline

| Review class | Target turnaround | Notes |
|-------------|-------------------|-------|
| A | 5 business days | Governance and administrative |
| B | 10 business days | Datasets, algorithms, compute |
| C | (reserved) | |
| D | 15 business days | Wet-lab data, expert review |

### Evidence standards

- All contributions must include the minimum required fields listed above.
- Datasets must include provenance: source, collection method, curation
  steps, and any exclusion criteria.
- Wet-lab data must follow the lab result schema
  (`schemas/lab_result.schema.json`) and include positive and negative
  controls.
- Algorithm contributions must include tests and a data-license declaration
  for any training or evaluation data.

### Publication rights

- Contributors retain ownership of their contributed data and methods.
- By contributing, you grant the OpenAMP project a non-exclusive,
  royalty-free license to use, reproduce, and redistribute the contribution
  for public-good purposes under the license you specify.
- You may publish your own results separately. We encourage preprints and
  open-access publication.

### Attribution

- All accepted contributions are recorded in the project's contribution
  registry (metadata: institution, contact, type, date, scope).
- Dataset and algorithm contributions are cited in the relevant
  documentation and benchmark cards.
- Contributors are listed in the project's acknowledgements section
  (unless they opt out).
- We follow academic citation norms for published work incorporated into
  the pipeline.

---

## Data governance

All contributed data is subject to:

- [`DATA_GOVERNANCE.md`](../trust/DATA_GOVERNANCE.md) — data handling,
  retention, and access policies.
- [`DATA_LICENSE_NOTICE.md`](../../DATA_LICENSE_NOTICE.md) — licensing terms
  for all data in the repository.

Key rules:

- Every dataset must declare a license from the approved list (CC0-1.0,
  CC-BY-4.0, CC-BY-SA-4.0, MIT, Apache-2.0, GPL-3.0, LGPL-2.1,
  BSD-2-Clause, BSD-3-Clause, ODbL-1.0, PDDL-1.0) or be reviewed by
  governance for restricted licenses (CC-BY-NC-4.0, custom, proprietary).
- Blocked licenses (unknown, unlicensed, all-rights-reserved) are never
  accepted.
- Contributors must confirm they have the right to share the data under
  the declared license.

---

## Safety constraints

- **Human review is required** before any wet-lab data or dual-use-relevant
  data enters the pipeline. This is enforced by the `human_review_required`
  flag, which must be `True` for `wet_lab_validation` contributions.
- **Dry-lab only.** Computational outputs are hypotheses and review aids.
  They are not biological proof.
- **No biological instructions.** Contributions must not contain detailed
  experimental protocols, dual-use information, or instructions for
  unsupervised biological work.
- Contributors must follow
  [`SAFETY.md`](../../SAFETY.md) and
  [`RESPONSIBLE_USE.md`](../../RESPONSIBLE_USE.md).

Contributions that violate these constraints will be rejected or sent back
for revision.

---

## Contact

- Governance: [`GOVERNANCE.md`](../../GOVERNANCE.md)
- Responsible use: [`RESPONSIBLE_USE.md`](../../RESPONSIBLE_USE.md)
- Safety: [`SAFETY.md`](../../SAFETY.md)
- Data governance: [`DATA_GOVERNANCE.md`](../trust/DATA_GOVERNANCE.md)

For questions, open a GitHub issue with the `institutional-contribution`
label, or contact the maintainers through the repository's discussion
board.
