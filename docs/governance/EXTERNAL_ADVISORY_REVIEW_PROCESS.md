# External Advisory Review Process

This document defines the process for external advisory review of OpenAMP Foundry
research outputs, governance decisions, and release candidates.

## Purpose

External review provides independent credibility for:
- Candidate selection rationale (why these sequences, not others)
- Benchmark honesty (do the benchmarks test what they claim?)
- Safety policy adequacy (are the safeguards sufficient?)
- Evidence package completeness (is the evidence ready for wet-lab partners?)

External review is **advisory only** — it does not replace the internal
governance process defined in GOVERNANCE.md.

## Reviewer Eligibility

External advisors must:
1. Hold a relevant domain expertise (antimicrobial peptide biology, ML benchmarking,
   biosafety policy, or open science governance)
2. Have no undisclosed conflict of interest (see COI_DISCLOSURE_TEMPLATE.md)
3. Agree in writing to the responsible use policy (RESPONSIBLE_USE.md)
4. Not be a current contributor to the OpenAMP Foundry codebase

## Review Scope

| Review type          | Trigger                                   | Reviewer count |
|----------------------|-------------------------------------------|----------------|
| Candidate review     | Before releasing a candidate list         | ≥ 2            |
| Benchmark audit      | Before updating a benchmark threshold     | ≥ 1            |
| Safety policy review | Before changing dual-use or safety policy | ≥ 2            |
| Evidence review      | Before releasing an evidence package      | ≥ 1            |
| Governance review    | Before changing the release policy        | ≥ 1            |

## Review Process

### Step 1: Prepare the review packet

The internal team prepares a review packet containing:
- The artifact or decision under review
- Relevant evidence and benchmarks
- Known limitations and open questions
- The specific questions the advisor is asked to answer

### Step 2: Assign and disclose

- Assign the review to an eligible advisor
- Request a COI disclosure (see COI_DISCLOSURE_TEMPLATE.md)
- Provide the advisor with the review packet and a deadline (default: 14 days)

### Step 3: Receive and log the review

- Receive the advisor's written review
- Log the review outcome in the decision log (DECISION_LOG.md)
- Note any findings that change the internal assessment

### Step 4: Respond to findings

For each advisory finding:
- **Critical finding**: halt release until resolved
- **Major finding**: resolve before release or document why not resolved
- **Minor finding**: document and address in next release cycle
- **Informational**: note in the evidence package

### Step 5: Close the review

- Record the review outcome in the governance decision log
- Update the artifact or decision record with the advisory review reference
- Release or defer based on the findings

## Machine-Validated Review Entries

Advisory review entries can be validated with:

```bash
openamp-foundry advisory-review-check --review-json '{"review_id": "ADV-2026-001", ...}'
```

See `src/openamp_foundry/governance/advisory_review.py` for the AdvisoryReview schema.

## Limitations

- This process validates review structure, not review quality
- External review does not guarantee correctness of the underlying research
- Reviewer availability may affect timelines
- The dry-lab-only constraint applies to all reviews: external advisors cannot
  certify wet-lab validity from computational evidence alone

## Linked Policies

- [GOVERNANCE.md](../../GOVERNANCE.md) — project governance structure
- [docs/governance/COI_DISCLOSURE_TEMPLATE.md](COI_DISCLOSURE_TEMPLATE.md) — conflict of interest
- [RESPONSIBLE_USE.md](../../RESPONSIBLE_USE.md) — responsible use
- [docs/governance/DECISION_LOG.md](DECISION_LOG.md) — governance decision log
- [docs/evidence/PROOF_LADDER.md](../evidence/PROOF_LADDER.md) — evidence ladder
