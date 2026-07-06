# Gold-Standard Calibration

> How do known literature AMPs score in the same pipeline as our candidates?
> This confirms that our scoring is calibrated against validated actives.

Generated: 2026-06-28T15:48:11.136196+00:00

## Confident panel score range (reference)

- Min ensemble: 0.796
- Max ensemble: 0.857
- Mean ensemble: 0.821

## Known AMP gold standards

| Name | Sequence | Activity | Safety | Ensemble | μH | Note |
|---|---|:---:|:---:|:---:|:---:|---|
| Melittin | `GIGAVLKVLTTGLPALISWI...` | 0.616 | 1.0 | 0.844 | 0.353 | Apis mellifera venom; hemolytic benchmark (WITHIN panel range) |
| Magainin-2 | `GIGKFLHSAKKFGKAFVGEI...` | 0.68 | 1.0 | 0.872 | 0.455 | Xenopus laevis frog skin; classical AMP (ABOVE panel) |
| LL-37 | `LLGDFFRKSKEKIGKEFKRI...` | 0.556 | 0.736 | 0.714 | 0.559 | Human cathelicidin; broad-spectrum (BELOW panel) |
| Cecropin-A | `KWKLFKKIEKVGQNIRDGII...` | 0.55 | 0.75 | 0.713 | 0.275 | Silk moth immunity; pioneer AMP (BELOW panel) |
| Defensin-HNP1 | `ACYCRIPACIAGERRYGTCI...` | 0.549 | 1.0 | 0.82 | 0.077 | Human neutrophil; β-sheet structure (WITHIN panel range) |
| Polymyxin-B1 | `XBDAXBBTBXBT` | — | — | — | — | Cyclic lipopeptide; last-resort MDR — placeholder (non-standard AA; skipped) |
| Temporin-A | `FLPLIGRVLSGIL` | 0.541 | 0.953 | 0.803 | 0.581 | Frog skin; short helix; similar to SEED-004 (WITHIN panel range) |

## Interpretation

If known active AMPs score **within or below** the panel's ensemble range, the
scoring is calibrated correctly — it values properties that literature validates.
If known AMPs score *far above* the panel, the panel may be under-optimised.
If known AMPs score *far below*, the panel may be over-scoring on non-AMP features.

## Panel candidates for reference

| ID | Ensemble | Activity | Safety |
|---|:---:|:---:|:---:|
| SEED-008_VAR_032 | 0.857 | 0.724 | 1.000 |
| SEED-007_VAR_009 | 0.849 | 0.697 | 1.000 |
| SEED-008_VAR_009 | 0.849 | 0.700 | 1.000 |
| SEED-008_VAR_019 | 0.845 | 0.690 | 1.000 |
| SEED-006_VAR_062 | 0.841 | 0.697 | 1.000 |
| SEED-008_VAR_044 | 0.832 | 0.692 | 1.000 |
| SEED-006_VAR_071 | 0.828 | 0.660 | 1.000 |
| SEED-007_VAR_001 | 0.824 | 0.662 | 1.000 |
| SEED-006_VAR_059 | 0.821 | 0.644 | 1.000 |
| SEED-003_VAR_017 | 0.816 | 0.832 | 0.992 |
| SEED-007_VAR_018 | 0.815 | 0.632 | 1.000 |
| SEED-006_VAR_006 | 0.812 | 0.616 | 1.000 |
| SEED-005_VAR_019 | 0.808 | 0.842 | 0.845 |
| SEED-009_VAR_027 | 0.808 | 0.640 | 1.000 |
| SEED-009_VAR_033 | 0.807 | 0.638 | 1.000 |
| SEED-003_VAR_012 | 0.807 | 0.816 | 0.981 |
| SEED-007_VAR_035 | 0.806 | 0.634 | 1.000 |
| SEED-001_VAR_064 | 0.802 | 0.806 | 1.000 |
| SEED-009_VAR_017 | 0.798 | 0.633 | 1.000 |
| SEED-009_VAR_039 | 0.796 | 0.624 | 1.000 |

## Blind spots (documented)

- **Melittin** — Safety=1.0 and μH=0.353 in the table above. The safety model assigns Melittin
  the maximum safety score despite its well-documented hemolytic activity (HC₅₀ ≈ 1–5 µg/mL
  in vitro). This is a confirmed model blind spot: the scorer does not detect hemolysis in
  cationic amphipathic sequences that lyse membranes via curvature-mediated mechanisms rather
  than charge alone. **Implication**: Safety=1.0 for panel candidates (including all four
  SEED-008 Trp-rich variants) cannot be used as evidence of non-hemolytic activity. Hemolysis
  must be assayed experimentally for every candidate regardless of safety score.
- **LL-37 and Cecropin-A** — both score below the panel floor (0.714 and 0.713 vs panel
  minimum 0.796). These are clinically relevant, well-characterised broad-spectrum AMPs. Their
  low scores indicate the pipeline's features are optimised for helical amphipathic AMPs of the
  magainin/mastoparan class. Candidates whose mechanism resembles LL-37 (helix-linker-helix) or
  Cecropin-A (long N-terminal amphipathic helix) are likely under-scored by this pipeline.
- **Defensin-HNP1** — β-sheet disulfide peptide; our scorer targets α-helical AMPs; lower score expected.
- **Polymyxin B** — cyclic lipopeptide with non-standard AA; not scorable by this pipeline.
- **Temporin-A** (`FLPLIGRVLSGIL`) — similar to frog-skin short-helix scaffolds excluded from
  the current panel (formerly SEED-004). Score 0.803 is within panel range, consistent with
  SEED-004-class sequences.

## Disclaimer

This calibration uses the same scoring model as candidate nomination. It is not
independent validation — it confirms internal consistency, not external predictive power.
The expanded AUROC benchmark (AUROC=0.7832 on 95 literature AMPs vs 96 background peptides;
PR #110) is the appropriate measure of pipeline discrimination performance. The original demo
set (AUROC=0.8420 on 43+44) is the historical baseline. Both are retrospective benchmarks,
not external prospective validation.
