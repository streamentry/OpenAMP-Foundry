# IP and Disclosure Plan

> **Purpose:** Strategic guidance for intellectual property decisions before public
> sequence disclosure. Not a legal opinion — consult a patent attorney before filing.
>
> **Last updated:** 2026-06-29 (Sprint 6)

---

## Patent Strategy

### Claimable Candidates

| Seed | Classification | Claim strategy |
|------|---------------|----------------|
| SEED-006 (4 candidates) | HIGH_CONFIDENCE_NOVEL | Primary patent claims — novel wasp-venom scaffold |
| SEED-007 (1 candidate) | HIGH_CONFIDENCE_NOVEL | Primary patent claims — novel bumblebee-venom scaffold |
| SEED-008 (3 candidates) | HIGH_CONFIDENCE_NOVEL | Primary patent claims — novel Trp-rich plant scaffold |
| SEED-009 (2 candidates) | HIGH_CONFIDENCE_NOVEL | Primary patent claims — novel proline-rich scaffold |
| SEED-007 (3 candidates) | NOVEL | Moderate claims — verify mechanism distinct from bombolitin literature |
| SEED-008 (1 candidate) | NOVEL | Moderate claims — verify mechanism distinct from indolicidin |
| SEED-005 (1 candidate) | CLOSE_RELATIVE | Not individually patentable — SAR control |
| SEED-001 (1 candidate) | KNOWN_VARIANT | Not patentable — positive control |
| SEED-003 (2 candidates) | KNOWN_VARIANT | Not patentable — tachyplesin-like SAR |

### Provisional Patent

Before any public sequence disclosure, file provisional patent application covering:
1. SEED-006 scaffold and all pilot variants
2. SEED-007 scaffold and all pilot variants
3. SEED-008 scaffold and all pilot variants
4. SEED-009 scaffold and all pilot variants
5. Composition claims for any MIC ≤ 8 µg/mL candidate
6. Methods of use (antimicrobial treatment, wound healing)

### Sequence Deposit

Deposit sequences in patent filing as SEQ ID NOs. Use the WIPO ST.26 standard
(valid from July 2022) for sequence listing.

## Disclosure Plan

| Tier | Candidates | Disclosure | Timing |
|:----:|------------|------------|--------|
| 1 | SEED-006, 007, 008, 009 (14 candidates) | **Redacted** from public repo | After provisional filing |
| 2 | SEED-001, 003, 005 (6 candidates) | Public (known scaffolds) | Anytime |
| 3 | Pipeline code | Public (MIT license) | Already public |

## Freedom to Operate

**Required searches before publication:**
- [ ] APD3 BLASTp — no hit > 80% identity
- [ ] DRAMP patent section — no overlapping claims
- [ ] Google Patents / Lens.org — scaffold-level search
- [ ] Competitor sequence database (AMP-Designer, AMPGAN v3, etc.)

---

## Wave 0.5 IP Addendum (2026-06-29)

Wave 0.5 added 10 new scaffold families. IP guidance by family:

| Family | Novelty Class | Claim Strategy |
|---|---|---|
| SEED-010 (histatin) | RELATED_NOVEL | Histatin-5/P-113 fragments are in clinical development (Cda1p binding); claim specific modifications (K4R, H13L), not the parent scaffold |
| SEED-011 (Pro-kinked) | HIGH_CONFIDENCE_NOVEL | Novel kinked-helix design; primary patent claim on kink-disrupted amphipathic motif |
| SEED-012 (Gly-rich) | HIGH_CONFIDENCE_NOVEL | Novel low-hydrophobicity cationic class; differentiated from defensins by sequence composition |
| SEED-013 (pleurocidin) | RELATED_NOVEL | Pleurocidin (Coulson 1996) is in the public domain; claim specific analogs with modifications |
| SEED-014 (cathelicidin-mini) | RELATED_NOVEL | Cathelicidin C-terminal domain widely patented; claim minimum-pharmacophore analogs |
| SEED-015 (KFLK de novo) | HIGH_CONFIDENCE_NOVEL | Fully de novo design; strong primary patent claim |
| SEED-016 (RRWK dual-Trp) | HIGH_CONFIDENCE_NOVEL | Novel dual-Trp low-aromatic design; distinguish from indolicidin and SEED-008 |
| SEED-017 (Pro-kinked Leu/Phe) | RELATED_NOVEL | Some overlap with proline-rich class; claim specific Pro-kink + Leu/Phe combination |
| SEED-018 (GKRK scattered-charge) | HIGH_CONFIDENCE_NOVEL | Novel charge-spacing pattern; strong claim |
| SEED-019 (Arg-Val alternating) | HIGH_CONFIDENCE_NOVEL | Novel Arg-Val beta-strand alternating motif; strong claim |

Wave 0.5 candidates in the final panel with REVIEW_REQUIRED patent risk (from novelty audit):
See `outputs/wave0_5_novelty_audit.csv`, `patent_risk` column.
All REVIEW_REQUIRED candidates must undergo FTO analysis before synthesis order.

## Publication Strategy

1. **First publication:** Pipeline methodology + benchmark results only
   (no candidate sequences disclosed)
2. **Second publication:** Candidate nominations + novelty audit
   (after provisional patent filing)
3. **Third publication:** Wet-lab results
   (after independent replication)

## Material Transfer

Before sharing candidate peptides with external labs, execute an MTA covering:
- Sequence confidentiality
- Publication rights
- IP ownership (background vs foreground)
- Data sharing obligations

## Contributor IP

All contributors to this repository have assigned code contributions under
the MIT license. No separate contributor agreement is in place for computational
contributions. If wet-lab collaborators join, a formal collaboration agreement
should define IP ownership before any experimental work begins.
