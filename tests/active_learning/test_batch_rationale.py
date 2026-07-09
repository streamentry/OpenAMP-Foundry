"""Tests for the batch-2 selection rationale report.

All data is synthetic. Tests verify code-path integrity, structure, and
honest role classification mechanics — not biological selection quality.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# ── Helpers ───────────────────────────────────────────────────────────


def _check_report_shape(report: dict) -> None:
    """Assert all required top-level fields exist."""
    required = [
        "version", "pool_size", "n_requested", "n_selected",
        "n_after_safety_gate", "n_gated_out",
        "ensemble_weight", "uncertainty_weight", "diversity_weight",
        "candidates", "role_summary", "role_descriptions",
        "selected_ids", "probes_in_top_n", "notes",
    ]
    for field in required:
        assert field in report, f"Missing field: {field}"


def _check_candidate_shape(candidate: dict) -> None:
    """Assert all required per-candidate fields exist."""
    required = [
        "candidate_id", "role", "ensemble_score", "uncertainty_score",
        "diversity_score", "ensemble_contribution", "uncertainty_contribution",
        "diversity_contribution", "combined_score",
        "passed_safety_gate", "safety_gate_reason", "explanation",
    ]
    for field in required:
        assert field in candidate, f"Missing candidate field: {field}"


# ── Tests ─────────────────────────────────────────────────────────────


class TestBatchRationaleReport:
    """Tests for the batch rationale report generation."""

    VALID_ROLES = {"exploit", "explore", "diversity", "combined"}

    def test_report_has_all_required_fields(self):
        """Report has all required top-level fields."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=5,
        )
        _check_report_shape(report.to_dict())

    def test_candidates_are_selected(self):
        """At least one candidate is selected with a small pool."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        assert report.n_selected > 0, "No candidates selected"
        assert len(report.candidates) == report.n_selected

    def test_per_candidate_required_fields(self):
        """Each candidate has all required fields."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        for c in report.to_dict()["candidates"]:
            _check_candidate_shape(c)

    def test_role_is_valid(self):
        """Each candidate has a valid role."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        for c in report.candidates:
            assert c.role in self.VALID_ROLES, (
                f"Invalid role: {c.role}"
            )

    def test_scores_in_valid_range(self):
        """Scores are between 0 and 1."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        for c in report.candidates:
            assert 0.0 <= c.ensemble_score <= 1.0
            assert 0.0 <= c.uncertainty_score <= 1.0
            assert 0.0 <= c.diversity_score <= 1.0
            assert 0.0 <= c.combined_score <= 1.0

    def test_role_summary_counts_match(self):
        """Role summary counts match the number of candidates per role."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        actual_counts: dict[str, int] = {}
        for c in report.candidates:
            actual_counts[c.role] = actual_counts.get(c.role, 0) + 1
        assert actual_counts == report.role_summary, (
            f"Role summary mismatch: {actual_counts} != {report.role_summary}"
        )

    def test_selected_ids_match_candidates(self):
        """Selected IDs list matches candidate IDs."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        candidate_ids = {c.candidate_id for c in report.candidates}
        assert set(report.selected_ids) == candidate_ids

    def test_probes_in_top_n_non_negative(self):
        """Probes count is non-negative."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        assert report.probes_in_top_n >= 0

    def test_notes_are_present(self):
        """Report has human-readable notes."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        assert len(report.notes) > 0
        assert any("Pool" in n for n in report.notes)

    def test_weight_config_matches_input(self):
        """Weights in report match the input weights."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
            ensemble_weight=0.50,
            uncertainty_weight=0.25,
            diversity_weight=0.25,
        )
        assert report.ensemble_weight == 0.50
        assert report.uncertainty_weight == 0.25
        assert report.diversity_weight == 0.25

    def test_write_json(self, tmp_path):
        """Writing to JSON produces valid file with expected fields."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
            write_rationale_json,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        out = tmp_path / "report.json"
        write_rationale_json(report, out)
        assert out.exists()
        data = json.loads(out.read_text())
        _check_report_shape(data)

    def test_write_markdown(self, tmp_path):
        """Writing to Markdown produces expected sections."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
            write_rationale_markdown,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        out = tmp_path / "report.md"
        write_rationale_markdown(report, out)
        assert out.exists()
        content = out.read_text()
        assert "# Batch-2 Selection Rationale Report" in content
        assert "## Overview" in content
        assert "## Selection Weights" in content
        assert "## Selection Breakdown by Role" in content
        assert "## Per-Candidate Rationale" in content
        assert "## Contribution Detail" in content
        assert "## Caveats" in content

    def test_cli_exits_zero(self):
        """CLI batch-rationale exits 0 and produces valid output."""
        result = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli",
                "batch-rationale",
                "--n-total", "20",
                "--n-active", "4",
                "--batch-size", "5",
                "--rng-seed", "42",
            ],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr[:500]}"
        data = json.loads(result.stdout)
        assert "version" in data
        assert "candidates" in data
        assert "role_summary" in data
        assert "selected_ids" in data

    def test_cli_writes_json_and_md(self, tmp_path):
        """CLI with --out-json and --out-md writes both files."""
        out_json = tmp_path / "report.json"
        out_md = tmp_path / "report.md"
        result = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli",
                "batch-rationale",
                "--n-total", "20",
                "--n-active", "4",
                "--batch-size", "5",
                "--out-json", str(out_json),
                "--out-md", str(out_md),
            ],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr[:500]}"
        assert out_json.exists()
        assert out_md.exists()
        data = json.loads(out_json.read_text())
        _check_report_shape(data)
        md_content = out_md.read_text()
        assert "# Batch-2 Selection Rationale Report" in md_content

    def test_schema_conformance(self, tmp_path):
        """JSON output validates against JSON Schema."""
        import jsonschema

        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "batch_rationale_report.schema.json"
        )
        schema = json.loads(schema_path.read_text())

        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
            write_rationale_json,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        out = tmp_path / "report.json"
        write_rationale_json(report, out)
        data = json.loads(out.read_text())

        jsonschema.validate(instance=data, schema=schema)

    def test_high_exploitation_weight_produces_exploit_roles(self):
        """High ensemble weight biases roles toward exploit."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
            ensemble_weight=0.90,
            uncertainty_weight=0.05,
            diversity_weight=0.05,
        )
        exploit_count = report.role_summary.get("exploit", 0)
        explore_count = report.role_summary.get("explore", 0)
        assert exploit_count > explore_count, (
            f"Expected more exploit ({exploit_count}) than explore ({explore_count}) "
            f"with high ensemble weight"
        )

    def test_all_selected_candidates_have_explanation(self):
        """Every selected candidate has a non-empty explanation."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        for c in report.candidates:
            assert len(c.explanation) > 0, (
                f"Empty explanation for {c.candidate_id}"
            )
            assert c.role in c.explanation.lower() or "balanced" in c.explanation.lower() or "exploration" in c.explanation.lower()

    def test_role_descriptions_are_present_for_all_roles(self):
        """Descriptions exist for all expected roles."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        for role in self.VALID_ROLES:
            assert role in report.role_descriptions, (
                f"Missing description for role: {role}"
            )
            assert len(report.role_descriptions[role]) > 0

    def test_empty_role_not_in_summary(self):
        """Roles with zero candidates should not appear in role_summary."""
        from openamp_foundry.active_learning.batch_rationale import (
            build_batch_rationale_report,
        )

        report = build_batch_rationale_report(
            n_total=30, n_active=5, batch_size=10,
        )
        for role, count in report.role_summary.items():
            assert count > 0, f"Role {role} has zero count but is in summary"
