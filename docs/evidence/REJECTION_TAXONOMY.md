# Rejection Reason Taxonomy

## Purpose

Standardized categories for why candidates are rejected by the pipeline. Enables analysis of failure patterns across batches.

## Categories

| Category | Description | Example |
|----------|-------------|---------|
| `sequence_invalid` | Sequence contains non-canonical amino acids or unparseable symbols. | "Sequence contains 'X' at position 5." |
| `length_out_of_range` | Sequence length outside configured min/max filter bounds. | "Length 6 outside filter range [8, 35]." |
| `novelty_below_threshold` | Similarity to a known reference exceeds the novelty cutoff. | "Nearest reference similarity 0.85 exceeds max 0.70." |
| `safety_risk_threshold` | Safety score below minimum (or risk score above maximum). | "Safety score 0.31 below minimum 0.50." |
| `synthesis_feasibility_low` | Synthesis feasibility score below viability threshold. | "Synthesis score 0.20 — multiple Trp residues with oxidation risk." |
| `disagreement_too_high` | Scorer disagreement exceeds max tolerance. | "Disagreement 0.85 exceeds max 0.50." |
| `diversity_filter_prune` | Removed by diversity selection to avoid near-duplicates. | "Similarity 0.82 to already-selected candidate." |
| `simulation_uncertainty_high` | Simulation proxy uncertainty exceeds 0.5 threshold. | "Max simulation uncertainty 0.92 exceeds 0.5." |
| `toxicity_risk_flagged` | Hemolysis or cytotoxicity risk above acceptable level. | "Hemolysis risk 0.89 flagged as HIGH." |

## Usage

Rejection categories are recorded in:
- Pipeline output JSONL (`known_failure_modes` field)
- Failed-candidate report output (if enabled)
- Negative-result archive entries

## Non-goals

This taxonomy does not cover:
- Wet-lab assay failures (e.g., synthesis failure, control failure) — see NEGATIVE_RESULT_ARCHIVE.md
- Human review rejections — see EXTERNAL_REVIEW_PACKET.md
- Safety or dual-use review rejections — see DUAL_USE_REVIEW.md
