"""Negative-set robustness tests — Phase 2 requirement.

AGENTS.md: "Negative-set robustness — Performance remains meaningful across multiple
negative datasets."

These tests verify that the pipeline enriches AMP-like positives over negatives
regardless of the type of negative control used:

  A. All-repeat / degenerate negatives (easy)     — already tested elsewhere
  B. Poly-cationic negatives (hard: high charge)  — new
  C. Poly-hydrophobic negatives (hard: high hydro) — new

A pipeline that only works on "easy" negatives (all-A, all-G) cannot be trusted.
A pipeline that works across all three negative types is more credible.

All scores are computational proxies. No biological activity is implied.
"""
from __future__ import annotations

import csv
from pathlib import Path

from openamp_foundry.benchmark.evaluate import enrichment_factor, recall_at_k
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.pipeline import score_candidates
from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.safety import safety_score


POSITIVES_CSV = "examples/benchmark/robustness_positives.csv"
NEGATIVE_A_CSV = "examples/negative/demo_negative_peptides.csv"
NEGATIVE_B_CSV = "examples/negative/poly_cationic.csv"
NEGATIVE_C_CSV = "examples/negative/poly_hydrophobic.csv"

POSITIVE_IDS = {"ROB-POS-001", "ROB-POS-002", "ROB-POS-003"}


def _merge_csv_files(pos_csv: str, neg_csv: str, tmp_path: Path) -> Path:
    """Combine a positive and negative CSV into a single candidate file."""
    out = tmp_path / "merged.csv"
    rows = []
    for path in [pos_csv, neg_csv]:
        with open(path) as f:
            reader = csv.DictReader(f)
            rows.extend(list(reader))
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "sequence", "source"])
        writer.writeheader()
        writer.writerows(rows)
    return out


class TestNegativeSetProperties:
    """Verify the negative datasets have the expected physicochemical profiles."""

    def test_poly_cationic_has_high_charge_low_hydrophobicity(self):
        features = compute_features("KKKKKKKKKKKKK")
        assert features["charge_density"] > 0.8, "Poly-K should have high charge density"
        assert features["hydrophobic_fraction"] == 0.0, "Poly-K should have zero hydrophobic fraction"

    def test_poly_hydrophobic_has_high_hydro_zero_charge(self):
        features = compute_features("LLLLLLLLLLLLL")
        assert features["hydrophobic_fraction"] == 1.0, "Poly-L should have 100% hydrophobic fraction"
        assert features["charge_density"] == 0.0, "Poly-L should have zero charge density"

    def test_poly_cationic_activity_score_below_real_amps(self):
        amp_feat = compute_features("KWKLFKKIGAVLKVL")
        polyk_feat = compute_features("KKKKKKKKKKKKK")
        amp_score = activity_likeness_score(amp_feat)
        polyk_score = activity_likeness_score(polyk_feat)
        assert amp_score > polyk_score, (
            f"Real AMP activity ({amp_score:.3f}) should exceed poly-K ({polyk_score:.3f}): "
            "poly-K has high charge but no hydrophobic face"
        )

    def test_poly_hydrophobic_activity_score_below_real_amps(self):
        amp_feat = compute_features("KWKLFKKIGAVLKVL")
        polyl_feat = compute_features("LLLLLLLLLLLLL")
        amp_score = activity_likeness_score(amp_feat)
        polyl_score = activity_likeness_score(polyl_feat)
        assert amp_score > polyl_score, (
            f"Real AMP activity ({amp_score:.3f}) should exceed poly-L ({polyl_score:.3f}): "
            "poly-L has no charge"
        )

    def test_poly_cationic_safety_penalized(self):
        polyk_feat = compute_features("KKKKKKKKKKKKK")
        polyk_safety = safety_score(polyk_feat)
        # Very high charge density should trigger the safety risk penalty
        assert polyk_safety < 0.7, (
            f"Poly-K safety={polyk_safety:.3f} should be <0.7 due to high charge density risk"
        )

    def test_poly_hydrophobic_safety_penalized(self):
        polyl_feat = compute_features("LLLLLLLLLLLLL")
        polyl_safety = safety_score(polyl_feat)
        # Very high hydrophobic fraction triggers hemolysis proxy penalty
        assert polyl_safety < 0.5, (
            f"Poly-L safety={polyl_safety:.3f} should be <0.5 due to extreme hydrophobicity"
        )

    def test_poly_repeat_long_run_detected(self):
        polyk_feat = compute_features("KKKKKKKKKKKKK")
        assert polyk_feat["longest_repeat_run"] == 13, "Poly-K should have repeat run of 13"

    def test_poly_cationic_file_exists(self):
        assert Path(NEGATIVE_B_CSV).exists(), "Poly-cationic negative set CSV not found"

    def test_poly_hydrophobic_file_exists(self):
        assert Path(NEGATIVE_C_CSV).exists(), "Poly-hydrophobic negative set CSV not found"


class TestEnrichmentAcrossNegativeSets:
    """Verify EF > 1.0 when positives are mixed with each negative set."""

    def test_enrichment_vs_degenerate_negatives(self, tmp_path):
        """Baseline: positives should easily outrank all-repeat / degenerate negatives."""
        merged = _merge_csv_files(POSITIVES_CSV, NEGATIVE_A_CSV, tmp_path)
        scored, _ = score_candidates(merged)
        k = len(POSITIVE_IDS)
        ef = enrichment_factor(scored, POSITIVE_IDS, k=k)
        assert ef > 1.0, f"EF={ef:.3f} should exceed 1.0 vs degenerate negatives"

    def test_enrichment_vs_poly_cationic_negatives(self, tmp_path):
        """Harder test: positives outrank high-charge-only negatives (poly-K/R)."""
        merged = _merge_csv_files(POSITIVES_CSV, NEGATIVE_B_CSV, tmp_path)
        scored, _ = score_candidates(merged)
        k = len(POSITIVE_IDS)
        ef = enrichment_factor(scored, POSITIVE_IDS, k=k)
        assert ef > 1.0, (
            f"EF={ef:.3f} should exceed 1.0 vs poly-cationic negatives. "
            "Pipeline must use BOTH charge and hydrophobicity, not just charge."
        )

    def test_enrichment_vs_poly_hydrophobic_negatives(self, tmp_path):
        """Harder test: positives outrank hydrophobic-only negatives (poly-L/I/V)."""
        merged = _merge_csv_files(POSITIVES_CSV, NEGATIVE_C_CSV, tmp_path)
        scored, _ = score_candidates(merged)
        k = len(POSITIVE_IDS)
        ef = enrichment_factor(scored, POSITIVE_IDS, k=k)
        assert ef > 1.0, (
            f"EF={ef:.3f} should exceed 1.0 vs poly-hydrophobic negatives. "
            "Pipeline must use BOTH charge and hydrophobicity, not just hydrophobicity."
        )

    def test_recall_at_k_vs_poly_cationic(self, tmp_path):
        """recall@3 should be 1.0 (all 3 positives in top 3) vs poly-cationic negatives."""
        merged = _merge_csv_files(POSITIVES_CSV, NEGATIVE_B_CSV, tmp_path)
        scored, _ = score_candidates(merged)
        rc = recall_at_k(scored, POSITIVE_IDS, k=3)
        assert rc == 1.0, (
            f"recall@3={rc:.4f}: all 3 known positives should be in the top 3 "
            "when mixed with 5 poly-cationic negatives"
        )

    def test_recall_at_k_vs_poly_hydrophobic(self, tmp_path):
        """recall@3 should be 1.0 (all 3 positives in top 3) vs poly-hydrophobic negatives."""
        merged = _merge_csv_files(POSITIVES_CSV, NEGATIVE_C_CSV, tmp_path)
        scored, _ = score_candidates(merged)
        rc = recall_at_k(scored, POSITIVE_IDS, k=3)
        assert rc == 1.0, (
            f"recall@3={rc:.4f}: all 3 known positives should be in the top 3 "
            "when mixed with 5 poly-hydrophobic negatives"
        )

    def test_ef_consistent_across_all_negative_sets(self, tmp_path):
        """EF > 1.0 for all three negative set types — robustness check."""
        results = {}
        for label, neg_csv in [
            ("degenerate", NEGATIVE_A_CSV),
            ("poly_cationic", NEGATIVE_B_CSV),
            ("poly_hydrophobic", NEGATIVE_C_CSV),
        ]:
            subdir = tmp_path / label
            subdir.mkdir()
            merged = _merge_csv_files(POSITIVES_CSV, neg_csv, subdir)
            scored, _ = score_candidates(merged)
            ef = enrichment_factor(scored, POSITIVE_IDS, k=len(POSITIVE_IDS))
            results[label] = ef

        failures = [
            f"{label} (EF={ef:.3f})"
            for label, ef in results.items()
            if ef <= 1.0
        ]
        assert not failures, (
            f"EF ≤ 1.0 for negative set(s): {failures}. "
            "Pipeline must beat random across all tested negative types."
        )

    def test_mean_positive_score_exceeds_mean_negative_across_all_sets(self, tmp_path):
        """Mean ensemble score of positives > mean of negatives for all negative types."""
        for label, neg_csv in [
            ("degenerate", NEGATIVE_A_CSV),
            ("poly_cationic", NEGATIVE_B_CSV),
            ("poly_hydrophobic", NEGATIVE_C_CSV),
        ]:
            subdir = tmp_path / label
            subdir.mkdir()
            merged = _merge_csv_files(POSITIVES_CSV, neg_csv, subdir)
            scored, _ = score_candidates(merged)

            pos_ensemble = [
                s.scores["ensemble"]
                for s in scored
                if s.candidate.candidate_id in POSITIVE_IDS
            ]
            neg_ensemble = [
                s.scores["ensemble"]
                for s in scored
                if s.candidate.candidate_id not in POSITIVE_IDS
            ]
            avg_pos = sum(pos_ensemble) / len(pos_ensemble)
            avg_neg = sum(neg_ensemble) / len(neg_ensemble)
            assert avg_pos > avg_neg, (
                f"[{label}] Mean positive ensemble ({avg_pos:.3f}) should exceed "
                f"mean negative ensemble ({avg_neg:.3f})"
            )
