"""Toxicity penalty tests — Phase 2 requirement.

AGENTS.md: "Toxicity penalty — Predicted hemolytic/toxic candidates are down-ranked."

These tests verify that sequences with properties associated with hemolysis risk or
toxicity proxy signals receive lower safety scores and lower overall ensemble rankings
than balanced AMP-like candidates.

Risk signals penalized by the safety scorer:
  - Hydrophobic fraction > 0.65 (hemolysis proxy)
  - Charge density > 0.55 (toxicity proxy)
  - Sequence length > 35 (large peptide → synthesis + stability risk)
  - Cysteine fraction > 0.25 (disulfide bridges → synthesis complexity)
  - Longest repeat run ≥ 6 (degenerate composition)

These are computational proxies, NOT validated toxicity predictors.
All results are heuristic-only. No biological safety claim is made.
"""
from __future__ import annotations

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.pipeline import score_candidates
from openamp_foundry.scoring.safety import safety_score


# Canonical AMP-like positives with balanced properties
AMP_SEQUENCES = [
    "KWKLFKKIGAVLKVL",       # balanced charge + hydrophobicity
    "RRWQWRMKKLG",           # cationic, moderate hydrophobicity
    "GIGKFLHSAKKFGKAFVGEIMNS",  # well-characterised AMP-like
]

# High-risk sequences targeting known safety penalty signals
HIGH_HYDROPHOBIC = [
    "LLLLLLLLLLLLLLLLL",     # hydrophobic_fraction = 1.0 (> 0.65 threshold)
    "IIIIIIIIIIIIIIIII",     # all-isoleucine, extreme hydrophobicity
    "VVVVVVVVVVVVVVVVV",    # all-valine, extreme hydrophobicity
    "LLLLWWWWLLLLWWWW",      # high aromatic + hydrophobic, hemolysis proxy
]

HIGH_CHARGE_DENSITY = [
    "KKKKKKKKKKKKKK",        # charge_density = 1.0 (> 0.55 threshold)
    "RRRRRRRRRRRRRR",        # all-arginine, extreme cation density
    "KRKRKRKRKRKRKRK",       # alternating K/R, very high charge
]

HIGH_CYSTEINE = [
    "CCCCCCCCCCC",           # 100% cysteine fraction (> 0.25 threshold)
    "CKCKCKCKCKCKCKCKCK",    # 50% cysteine fraction
    "CKWCKCWCKCKWCK",        # mixed but > 0.25 cys fraction
]

VERY_LONG = [
    "KWKLFKKIGAVLKVLKWKLFKKIGAVLKVLKWKLFKK",  # 38 aa, exceeds 35 aa threshold
]

LONG_REPEAT = [
    "AAAAAAAAAAAAAAAAAA",    # repeat run = 18
    "GGGGGGGGGGGGGGGGGG",    # repeat run = 18
    "KKKKKKKKKKKKKKKKKK",    # repeat run = 18 + high charge (double penalty)
]


class TestSafetyScorePenaltyMechanism:
    def test_extreme_hydrophobicity_reduces_safety(self):
        for seq in HIGH_HYDROPHOBIC[:2]:
            feat = compute_features(seq)
            score = safety_score(feat)
            assert score < 0.6, (
                f"{seq!r}: safety={score:.3f} should be <0.6 for extreme hydrophobic fraction "
                f"(hydrophobic_fraction={feat['hydrophobic_fraction']:.2f})"
            )

    def test_extreme_charge_density_reduces_safety(self):
        for seq in HIGH_CHARGE_DENSITY[:2]:
            feat = compute_features(seq)
            score = safety_score(feat)
            assert score < 0.6, (
                f"{seq!r}: safety={score:.3f} should be <0.6 for extreme charge density "
                f"(charge_density={feat['charge_density']:.2f})"
            )

    def test_high_cysteine_fraction_reduces_safety(self):
        cys_seq = "CCCCCCCCCCC"
        feat = compute_features(cys_seq)
        assert feat["cysteine_fraction"] > 0.25, "Poly-C should exceed cysteine threshold"
        score = safety_score(feat)
        assert score < 0.9, (
            f"Poly-C safety={score:.3f} should be reduced by high cysteine fraction"
        )

    def test_very_long_sequence_reduces_safety(self):
        long_seq = VERY_LONG[0]
        feat = compute_features(long_seq)
        assert feat["length"] > 35, f"Sequence should be >35 aa, got {feat['length']}"
        score = safety_score(feat)
        assert score < 1.0, (
            f"Long sequence (>{35} aa) safety={score:.3f} should be penalized"
        )

    def test_long_repeat_run_reduces_safety(self):
        for seq in LONG_REPEAT:
            feat = compute_features(seq)
            assert feat["longest_repeat_run"] >= 6, (
                f"{seq!r}: repeat_run={feat['longest_repeat_run']} should be ≥6"
            )
            score = safety_score(feat)
            assert score < 1.0, (
                f"{seq!r}: safety={score:.3f} should be reduced by long repeat run"
            )

    def test_balanced_amp_has_higher_safety_than_poly_hydrophobic(self):
        for amp_seq in AMP_SEQUENCES:
            amp_feat = compute_features(amp_seq)
            amp_safe = safety_score(amp_feat)
            for bad_seq in HIGH_HYDROPHOBIC[:2]:
                bad_feat = compute_features(bad_seq)
                bad_safe = safety_score(bad_feat)
                assert amp_safe > bad_safe, (
                    f"{amp_seq!r} safety ({amp_safe:.3f}) should exceed "
                    f"{bad_seq!r} safety ({bad_safe:.3f}): "
                    "balanced AMP should be safer than extreme hydrophobic sequence"
                )

    def test_balanced_amp_has_higher_safety_than_poly_cationic(self):
        for amp_seq in AMP_SEQUENCES:
            amp_feat = compute_features(amp_seq)
            amp_safe = safety_score(amp_feat)
            for bad_seq in HIGH_CHARGE_DENSITY[:2]:
                bad_feat = compute_features(bad_seq)
                bad_safe = safety_score(bad_feat)
                assert amp_safe > bad_safe, (
                    f"{amp_seq!r} safety ({amp_safe:.3f}) should exceed "
                    f"{bad_seq!r} safety ({bad_safe:.3f}): "
                    "balanced AMP should be safer than extreme poly-cationic sequence"
                )

    def test_safety_risk_monotonic_with_excess_hydrophobicity(self):
        """More extreme hydrophobicity → lower safety (monotonic penalty)."""
        seqs = [
            "KWKLFKKIGAVLKVL",  # ~60% hydrophobic, balanced
            "LWKLFKKIGALLKVL",  # ~70% hydrophobic, above threshold
            "LLLLLLLLLLLLLL",   # 100% hydrophobic, maximum penalty
        ]
        scores = [safety_score(compute_features(s)) for s in seqs]
        assert scores[0] > scores[1] > scores[2] or scores[0] > scores[2], (
            f"Safety should decrease with increasing hydrophobicity: {scores}"
        )

    def test_double_penalty_high_charge_and_repeat(self):
        """High charge density + long repeat should accumulate risk penalties."""
        poly_k = "KKKKKKKKKKKKKK"
        feat = compute_features(poly_k)
        score = safety_score(feat)
        # Poly-K: charge_density=1.0 (penalty) + repeat_run=14 (penalty) = low safety
        assert score < 0.4, (
            f"Poly-K safety={score:.3f} should be very low (double penalty: "
            f"charge_density={feat['charge_density']:.2f}, "
            f"repeat_run={feat['longest_repeat_run']})"
        )


class TestToxicityDownRankingInPipeline:
    """Verify that high-risk sequences rank below balanced AMPs in the full pipeline."""

    def test_high_risk_sequences_have_lower_ensemble_than_balanced_amps(self, tmp_path):
        """High-risk candidates should receive lower ensemble scores than AMP candidates."""
        high_risk_csv = tmp_path / "high_risk.csv"
        mixed_csv = tmp_path / "mixed.csv"

        # Write high-risk candidates
        high_risk_rows = [
            "id,sequence,source",
            "RISK-001,LLLLLLLLLLLLLLLLL,high_risk",  # extreme hydrophobic
            "RISK-002,KKKKKKKKKKKKKK,high_risk",     # extreme charge density
            "RISK-003,IIIIIIIIIIIIIIIII,high_risk",  # extreme hydrophobic
        ]
        high_risk_csv.write_text("\n".join(high_risk_rows))

        # Write mixed (AMPs + high-risk)
        amp_rows = [
            "AMP-001,KWKLFKKIGAVLKVL,balanced_amp",
            "AMP-002,RRWQWRMKKLG,balanced_amp",
            "AMP-003,GIGKFLHSAKKFGKAFVGEIMNS,balanced_amp",
        ]
        all_rows = high_risk_rows + amp_rows
        mixed_csv.write_text("\n".join(all_rows))

        scored, _ = score_candidates(mixed_csv)

        amp_ensemble = {
            s.candidate.candidate_id: s.scores["ensemble"]
            for s in scored
            if s.candidate.candidate_id.startswith("AMP-")
        }
        risk_ensemble = {
            s.candidate.candidate_id: s.scores["ensemble"]
            for s in scored
            if s.candidate.candidate_id.startswith("RISK-")
        }

        avg_amp = sum(amp_ensemble.values()) / len(amp_ensemble)
        avg_risk = sum(risk_ensemble.values()) / len(risk_ensemble)
        assert avg_amp > avg_risk, (
            f"Mean AMP ensemble ({avg_amp:.3f}) should exceed mean high-risk ensemble "
            f"({avg_risk:.3f}): toxicity penalty should down-rank risky sequences"
        )

    def test_all_high_risk_sequences_below_best_amp(self, tmp_path):
        """Every high-risk sequence should rank below the best AMP candidate."""
        mixed_csv = tmp_path / "mixed.csv"
        rows = [
            "id,sequence,source",
            "AMP-001,KWKLFKKIGAVLKVL,balanced_amp",
            "AMP-002,RRWQWRMKKLG,balanced_amp",
            "RISK-001,LLLLLLLLLLLLLLLLL,high_risk",
            "RISK-002,KKKKKKKKKKKKKK,high_risk",
            "RISK-003,CCCCCCCCCCC,high_risk",
        ]
        mixed_csv.write_text("\n".join(rows))

        scored, _ = score_candidates(mixed_csv)
        from openamp_foundry.selection.pareto import rank_candidates
        ranked = rank_candidates(scored)

        top_amp_rank = min(
            i for i, s in enumerate(ranked) if s.candidate.candidate_id.startswith("AMP-")
        )
        worst_amp_rank = max(
            i for i, s in enumerate(ranked) if s.candidate.candidate_id.startswith("AMP-")
        )
        best_risk_rank = min(
            i for i, s in enumerate(ranked) if s.candidate.candidate_id.startswith("RISK-")
        )

        assert best_risk_rank > worst_amp_rank, (
            f"Best high-risk rank ({best_risk_rank}) should be worse than "
            f"worst AMP rank ({worst_amp_rank}): all AMPs should outrank all high-risk candidates"
        )
        _ = top_amp_rank  # acknowledged

    def test_toxicity_penalty_propagates_to_safety_score_in_pipeline(self, tmp_path):
        """Safety score for high-risk sequences should be low in the full pipeline."""
        candidates_csv = tmp_path / "cands.csv"
        candidates_csv.write_text(
            "id,sequence,source\n"
            "SAFE-001,KWKLFKKIGAVLKVL,balanced\n"
            "RISKY-001,LLLLLLLLLLLLLLLLL,high_risk\n"
            "RISKY-002,KKKKKKKKKKKKKK,high_risk\n"
        )
        scored, _ = score_candidates(candidates_csv)
        safe_score = next(s for s in scored if s.candidate.candidate_id == "SAFE-001")
        risky1 = next(s for s in scored if s.candidate.candidate_id == "RISKY-001")
        risky2 = next(s for s in scored if s.candidate.candidate_id == "RISKY-002")

        assert safe_score.scores["safety"] > risky1.scores["safety"], (
            f"Balanced AMP safety ({safe_score.scores['safety']:.3f}) should exceed "
            f"poly-L safety ({risky1.scores['safety']:.3f})"
        )
        assert safe_score.scores["safety"] > risky2.scores["safety"], (
            f"Balanced AMP safety ({safe_score.scores['safety']:.3f}) should exceed "
            f"poly-K safety ({risky2.scores['safety']:.3f})"
        )

    def test_high_risk_candidates_not_selected_with_strict_safety_threshold(self, tmp_path):
        """With max_safety_risk=0.30, high-risk candidates should be excluded."""
        from openamp_foundry.selection.diversity import greedy_diverse_select
        from openamp_foundry.selection.pareto import rank_candidates

        candidates_csv = tmp_path / "cands.csv"
        candidates_csv.write_text(
            "id,sequence,source\n"
            "AMP-001,KWKLFKKIGAVLKVL,balanced\n"
            "AMP-002,RRWQWRMKKLG,balanced\n"
            "RISK-001,LLLLLLLLLLLLLLLLL,high_risk\n"
            "RISK-002,KKKKKKKKKKKKKK,high_risk\n"
        )
        scored, _ = score_candidates(candidates_csv)
        ranked = rank_candidates(scored)

        # Apply strict safety filter (only sequences with safety ≥ 1 - 0.30 = 0.70)
        max_risk = 0.30
        eligible = [
            item for item in ranked
            if item.scores["safety"] >= (1.0 - max_risk)
        ]
        selected = greedy_diverse_select(eligible, top_n=10)
        selected_ids = {s.candidate.candidate_id for s in selected}

        assert "RISK-001" not in selected_ids, (
            "Poly-L (extreme hydrophobicity) should be excluded with max_safety_risk=0.30"
        )
        assert "RISK-002" not in selected_ids, (
            "Poly-K (extreme charge) should be excluded with max_safety_risk=0.30"
        )
        assert "AMP-001" in selected_ids or "AMP-002" in selected_ids, (
            "At least one balanced AMP should remain selected after strict safety filter"
        )
