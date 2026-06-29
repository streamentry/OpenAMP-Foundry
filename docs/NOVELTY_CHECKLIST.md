# Novelty Verification Checklist

> **Before publication or contacting labs:** Confirm pilot-panel novelty against public
> sequence databases. The pipeline's internal novelty check (72-AMP curated reference;
> 16/20 NOVEL, 3 KNOWN_VARIANT, 1 CLOSE_RELATIVE) is a preliminary screen — not sufficient
> for publication claims. This checklist covers the full external verification.

---

## Step 1 — BLASTp against UniProt/Swiss-Prot

| Tool | URL | Action |
|------|-----|--------|
| NCBI BLASTp | https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE=Proteins | Submit all 20 sequences; filter to "UniProtKB/Swiss-Prot" database; record top hit E-value, identity %, and species |
| UniProt BLAST | https://www.uniprot.org/blast | Cross-check against curated UniProt antimicrobial sequence set |

**Criteria:**
- E-value < 1e-5 AND identity > 80% → KNOWN_VARIANT (not publication-novel)
- E-value < 1e-5 AND identity 50–80% → CLOSE_RELATIVE (requires mechanism justification)
- No significant hit → NOVEL (strongest claim)

## Step 2 — Specialised AMP databases

| Database | URL | Scope | Submission method |
|----------|-----|-------|-------------------|
| **APD3** (Antimicrobial Peptide Database v3) | https://aps.unmc.edu/AP/ | > 3,000 natural AMPs from 6 kingdoms | Paste FASTA sequences into search box; records family, source organism, MIC |
| **DRAMP v3.0** | http://dramp.cpu-bioinfor.org/ | > 19,000 entries including synthetic AMPs | Sequence search; also has patent-derived section |
| **dbAMP 2.0** | https://awi.cuhk.edu.cn/dbAMP/ | > 4,000 validated AMPs with activity spectra | Sequence-based search or upload FASTA |
| **LAMP2** | http://biotechlab.fudan.edu.cn/database/lamp | > 5,500 AMPs with experimental MIC data | BLAST search against database |
| **CAMPR4** | http://www.camp3.bicnirrh.res.in/ | Collection of sequences + structures + family information | Use both the prediction tool AND the database BLAST |

**Check each candidate against:**
- [ ] APD3 — no hit > 80% identity
- [ ] DRAMP v3.0 — no hit > 80% identity (check patent section separately)
- [ ] dbAMP 2.0 — no hit > 80% identity
- [ ] CAMPR4 sequence database — no hit > 80% identity

## Step 3 — Patent search

| Database | URL | Query |
|----------|-----|-------|
| Google Patents | https://patents.google.com/ | Search "antimicrobial peptide" + candidate sequence substring (first 8 AA) |
| WIPO PATENTSCOPE | https://patentscope.wipo.int/ | Full sequence search if available; otherwise BLAST against patent sequences |
| USPTO | https://patft.uspto.gov/ | Quick text search for unique sequence motif |

**Check:**
- [ ] No patent claims the same or near-identical sequence
- [ ] No patent claims the same scaffold with conservative substitutions at the same positions

## Step 4 — RCSB (Protein Data Bank) structure search

For helical candidates, check whether the 3D structure of an identical or near-identical
sequence has been solved (NMR, X-ray, cryo-EM):

- URL: https://www.rcsb.org/
- Search by: Sequence BLAST against PDB sequences
- **Check:** Any solved structure with > 90% identity over the candidate length

## Step 5 — Literature search (PubMed)

For each candidate family, run a targeted PubMed search:

```text
(candidate_name OR seed_sequence_motif) AND antimicrobial
```

E.g. for SEED-008:
```text
(FPVTWRWWKWYRG OR puroindoline Trp domain) AND antimicrobial
```

**Check:**
- [ ] No prior publication with the same sequence
- [ ] No prior publication with the same scaffold and demonstrated antimicrobial activity

---

## Results Table

| Rank | Candidate | BLASTp top hit | APD3 | DRAMP | dbAMP | Patent | PDB | Lit. search | Verdict |
|:----:|-----------|:---:|:----:|:-----:|:-----:|:------:|:---:|:-----------:|:-------:|
| 1 | SEED-009_VAR_033 | | | | | | | | |
| 2 | SEED-009_VAR_027 | | | | | | | | |
| 3 | SEED-007_VAR_009 | | | | | | | | |
| 4 | SEED-007_VAR_001 | | | | | | | | |
| ... | (all 20) | | | | | | | | |

Use 72-AMP broad novelty check (`docs/NOVELTY_BROAD_CHECK.md`) as internal baseline.
The external checks above are required before publishing novelty claims.

---

## Interpretive Guidance

| Verdict | Meaning | Publication strategy |
|---------|---------|---------------------|
| NOVEL (< 50% identity to any known AMP) | Candidate sequence is genuinely new | Claim "novel antimicrobial peptide family"; strongest publication position |
| CLOSE_RELATIVE (50–70% identity) | Related to known family but distinct | Claim "novel variant of [family]"; highlight mechanism or potency differences |
| KNOWN_VARIANT (> 70% identity) | Near-copy of published sequence | Cannot claim novelty; publish as "SAR study of [known AMP]" if potency is exceptional |
| PATENTED | Sequence or scaffold is IP-protected | DO NOT publish without legal review; consider license or alternative scaffold |

---

## Disclaimer

Computational novelty (Levenshtein distance against curated references) is not a substitute
for database-level sequence search. Even after these checks, a published AMP that is absent
from these databases could invalidate a novelty claim. The most defensible novelty claim
requires all checks above to return "no significant hit" for the candidate family.
