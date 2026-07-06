# Postmortem: SEED-020 Novelty Check Used Wrong Database — Patent Risk Missed

**Date:** 2026-06-29  
**Severity:** HIGH — incorrect safety/IP claim propagated into wet-lab handoff documents  
**PRs involved:** #109 (introduced error), #110 (corrected)  
**Status:** Resolved

---

## What Happened

Wave 0.5b screening confirmed SEED-020_VAR_004 (RLRIRVLKRLLK) and SEED-020_VAR_002
(KVRIRVLKRLLK) as the top candidates by external predictor consensus. A novelty check was
run before adding them to the final panel. That check returned **NOVEL** for both, and the
result was documented in `WET_LAB_HANDOFF.md` and `EXPERT_REVIEW_PACK.md` as:

> "Both confirmed NOVEL by broad novelty check (72-AMP curated DB; <50% max similarity; **no
> patent DB matches**)."

This claim was **wrong**. The full BLOSUM62 audit (27,234 sequences, including the DRAMP
patent sub-database) later showed:

| Candidate | Sequence | Identity | Hit | Patent? |
|-----------|----------|----------|-----|---------|
| SEED-020_VAR_004 | RLRIRVLKRLLK | 75% | DRAMP05502 | Yes |
| SEED-020_VAR_002 | KVRIRVLKRLLK | 67% | DRAMP05504 | Yes |
| SEED-019_VAR_004 | RVRIRLVKRLLK | 66.7% | DRAMP05502 | Yes |

All three are **CLOSE_RELATIVE / POSSIBLE_PATENT_RISK**, not NOVEL.

The error was caught by user review ("but have you checked novel carefully?") and corrected
in PR #110 before any synthesis orders were placed.

---

## Root Cause

Two separate novelty-checking tools exist in this codebase:

| Tool | Database | Sequences | Includes patents? |
|------|----------|-----------|-------------------|
| `novelty-check-broad` CLI | `examples/known_reference/amp_curated_references.csv` | **72** | **No** |
| `scripts/run_wave0_5_novelty_audit_v2.py` | `data/novelty_db/*.fasta` | **27,234** | **Yes** |

The preliminary check (`novelty-check-broad`) was run instead of the full audit
(`run_wave0_5_novelty_audit_v2.py`). The 72-sequence database was originally built as a
quick sanity-check tool. It has no patent sequences. At 72 sequences it cannot catch
near-duplicates of the ~18,715 DRAMP patent entries.

The SEED-020 Arg-Ile/Val/Leu scaffold shares its C-terminal RLLK repeat with DRAMP05502
(RLLKQWPIGRLLKRLLKRLLK). The 72-sequence database contains nothing similar, so the
preliminary check returned low similarity and labelled both candidates NOVEL — a true
negative in a too-small reference set, not a true novel finding.

### Contributing factors

1. **No gate enforcing full-DB audit before panel addition.** The workflow for adding a
   candidate to `wave1_final_panel.csv` had no check requiring the `run_wave0_5_novelty_audit_v2`
   result to be present. The preliminary tool output was accepted as sufficient.

2. **Similar tool names with very different scope.** `novelty-check-broad` sounds
   authoritative; the "broad" qualifier refers to comparing against more classes than the
   seed-based check, not to the database being large or patent-inclusive.

3. **Result documented without citing which DB was used.** The PR #109 docs said "no patent
   DB matches" without stating that the check had not actually queried a patent database.

4. **No cross-file consistency check between preliminary and full audit outputs.** The full
   audit CSV (`outputs/wave0_5_novelty_audit_v2.csv`) already existed and already classified
   SEED-019_VAR_004 as CLOSE_RELATIVE + POSSIBLE_PATENT_RISK via DRAMP05502. The SEED-020
   candidates were not in that file yet (they were new), but the DRAMP05502 flag on the parent
   scaffold SEED-019_VAR_004 was a direct warning sign that was not noticed before adding the
   SEED-020 variants.

---

## Impact

- Two candidates incorrectly labelled NOVEL in merged docs for ~hours.
- If the error had not been caught: synthesis could have been ordered for patent-proximal
  peptides without IP clearance, creating IP liability and potentially wasted synthesis spend.
- No synthesis was ordered; no wet-lab work was affected.

---

## Resolution

PR #110 corrected both documents:

- `docs/review/WET_LAB_HANDOFF.md`: table corrected, IP NOTE expanded to all three SEED-019/020
  candidates with DRAMP accession numbers, Novelty prose rewritten, VAR_008 added as the
  CLEAR (no patent hit) fallback.
- `docs/review/EXPERT_REVIEW_PACK.md`: family table and wave 0.5b addendum rewritten; explicit
  ⚠ correction block added naming the DRAMP05502/05504 alignments.
- Local `outputs/wave1_final_panel.csv`: novelty_class corrected to CLOSE_RELATIVE for
  VAR_004 and VAR_002 with POSSIBLE_PATENT_RISK noted.

---

## Preventive Actions

### Immediate

- [x] **PR #110 merged** — corrected novelty status in all handoff documents.
- [x] **This postmortem** — records the failure mode for future reference.

### Process changes required before next wave

1. **Mandatory full-DB audit gate** — Before any candidate is added to
   `wave1_final_panel.csv`, `scripts/run_wave0_5_novelty_audit_v2.py` output must exist for
   that candidate in `outputs/wave0_5_novelty_audit_v2.csv`. The 72-sequence preliminary check
   may still be used as a fast early filter but must never be the sole source for a novelty
   claim in a submission document.

2. **Rename or deprecate `novelty-check-broad` CLI** — The "broad" label is misleading.
   Either rename to `novelty-check-preliminary` (72-seq, no patents, fast sanity check only)
   or add a prominent warning to its output header:
   ```
   WARNING: This check uses 72 sequences and does NOT query patent databases.
   For panel additions and submission documents, use run_wave0_5_novelty_audit_v2.py.
   ```

3. **Scaffold continuity check** — When adding a candidate from a seed family that already
   has a POSSIBLE_PATENT_RISK entry in the full audit, run the full audit on the new variant
   before documentation. SEED-020 variants are scaffolded from SEED-019_VAR_004, which was
   already flagged. This flag should have triggered a full-DB check automatically.

4. **Document novelty source in every claim** — Any novelty statement in a submission
   document must cite the specific DB used and its size, e.g.:
   - ✓ "CLOSE_RELATIVE (75% to DRAMP05502, full 27,234-seq audit v2, 2026-06-29)"
   - ✗ "NOVEL by broad novelty check"

5. **PRE_WET_LAB_CHECKLIST.md update** — Add an explicit gate:
   > - [ ] All candidates in `wave1_final_panel.csv` have a row in
   >   `outputs/wave0_5_novelty_audit_v2.csv` (full BLOSUM62, 27,234-seq DB, includes patents).
   >   No candidate with only a 72-seq preliminary result may appear in the panel.

---

## Lessons Learned

| Lesson | Application |
|--------|-------------|
| A tool named "broad" may still be narrow | Always check the database size and patent coverage before citing a novelty result |
| Parent-scaffold patent flags propagate to children | If scaffold S has a patent hit, all S-derived variants must be re-audited with the full DB |
| Document the DB, not just the result | "NOVEL" without citing the DB and sequence count is not a reproducible claim |
| Pre-registration discipline catches errors before they reach the CRO | The assay pre-registration + handoff review workflow created the opportunity for this catch |

---

## Timeline

| Time | Event |
|------|-------|
| 2026-06-29 AM | Wave 0.5b screening completes; user provides external predictor results |
| 2026-06-29 | `novelty-check-broad` (72-seq) run on SEED-020 top candidates; returns NOVEL |
| 2026-06-29 | PR #109 opened and merged with incorrect "NOVEL / no patent DB matches" claim |
| 2026-06-29 | User asks "but have you checked novel carefully?" |
| 2026-06-29 | Full BLOSUM62 audit (27,234-seq) run; DRAMP05502/05504 patent hits discovered |
| 2026-06-29 | PR #110 opened, code-reviewed, corrected, merged |
| 2026-06-29 | This postmortem written |
