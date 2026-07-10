"""Tests for benchmark_governance module (C10)."""
import os
import tempfile
from pathlib import Path

import pytest

from openamp_foundry.evidence.benchmark_governance import (
    GOVERNED_SCRIPTS,
    SCRIPT_TO_BMC_ID,
    BenchmarkGovernanceError,
    GovernanceReport,
    _discover_scripts,
    check_governance,
    format_governance_report,
)


# --- Fixtures and helpers ---

class _FakeCard:
    def __init__(self, bmc_id: str):
        self.bmc_id = bmc_id


def _make_registry(*bmc_ids: str) -> dict:
    return {bmc_id: _FakeCard(bmc_id) for bmc_id in bmc_ids}


def _make_scripts_dir(filenames: list[str]) -> str:
    tmpdir = tempfile.mkdtemp()
    for name in filenames:
        Path(tmpdir, name).write_text("# placeholder")
    return tmpdir


# --- Constants ---

class TestConstants:
    def test_governed_scripts_is_frozenset(self):
        assert isinstance(GOVERNED_SCRIPTS, frozenset)

    def test_script_to_bmc_id_is_dict(self):
        assert isinstance(SCRIPT_TO_BMC_ID, dict)

    def test_governed_scripts_matches_mapping_keys(self):
        assert GOVERNED_SCRIPTS == frozenset(SCRIPT_TO_BMC_ID.keys())

    def test_precision_at_k_is_governed(self):
        assert "benchmark_precision_at_k.py" in GOVERNED_SCRIPTS

    def test_charge_matched_is_governed(self):
        assert "benchmark_charge_matched.py" in GOVERNED_SCRIPTS

    def test_calibration_is_governed(self):
        assert "benchmark_calibration.py" in GOVERNED_SCRIPTS

    def test_per_family_is_governed(self):
        assert "benchmark_per_family.py" in GOVERNED_SCRIPTS

    def test_cheap_enemy_comparison_is_governed(self):
        assert "benchmark_cheap_enemy_comparison.py" in GOVERNED_SCRIPTS

    def test_precision_at_k_maps_to_bmc_0001(self):
        assert SCRIPT_TO_BMC_ID["benchmark_precision_at_k.py"] == "BMC-0001"

    def test_charge_matched_maps_to_bmc_0002(self):
        assert SCRIPT_TO_BMC_ID["benchmark_charge_matched.py"] == "BMC-0002"

    def test_calibration_maps_to_bmc_0003(self):
        assert SCRIPT_TO_BMC_ID["benchmark_calibration.py"] == "BMC-0003"

    def test_per_family_maps_to_bmc_0004(self):
        assert SCRIPT_TO_BMC_ID["benchmark_per_family.py"] == "BMC-0004"

    def test_cheap_enemy_maps_to_bmc_0005(self):
        assert SCRIPT_TO_BMC_ID["benchmark_cheap_enemy_comparison.py"] == "BMC-0005"

    def test_five_governed_scripts(self):
        assert len(GOVERNED_SCRIPTS) == 5

    def test_all_bmc_ids_have_prefix(self):
        for bmc_id in SCRIPT_TO_BMC_ID.values():
            assert bmc_id.startswith("BMC-"), f"{bmc_id} should start with BMC-"


# --- BenchmarkGovernanceError ---

class TestBenchmarkGovernanceError:
    def test_is_exception(self):
        assert issubclass(BenchmarkGovernanceError, Exception)

    def test_can_be_raised_with_message(self):
        with pytest.raises(BenchmarkGovernanceError, match="test message"):
            raise BenchmarkGovernanceError("test message")


# --- _discover_scripts ---

class TestDiscoverScripts:
    def test_empty_dir(self):
        tmpdir = tempfile.mkdtemp()
        assert _discover_scripts(tmpdir) == []

    def test_nonexistent_dir(self):
        assert _discover_scripts("/nonexistent/path/12345") == []

    def test_finds_benchmark_scripts(self):
        tmpdir = _make_scripts_dir(["benchmark_a.py", "benchmark_b.py"])
        result = _discover_scripts(tmpdir)
        assert "benchmark_a.py" in result
        assert "benchmark_b.py" in result

    def test_ignores_non_benchmark_files(self):
        tmpdir = _make_scripts_dir(["utils.py", "benchmark_a.py", "README.md"])
        result = _discover_scripts(tmpdir)
        assert result == ["benchmark_a.py"]

    def test_ignores_non_py_files(self):
        tmpdir = _make_scripts_dir(["benchmark_a.sh", "benchmark_b.py"])
        result = _discover_scripts(tmpdir)
        assert result == ["benchmark_b.py"]

    def test_returns_sorted(self):
        tmpdir = _make_scripts_dir(["benchmark_z.py", "benchmark_a.py", "benchmark_m.py"])
        result = _discover_scripts(tmpdir)
        assert result == sorted(result)

    def test_returns_filenames_not_paths(self):
        tmpdir = _make_scripts_dir(["benchmark_test.py"])
        result = _discover_scripts(tmpdir)
        assert result == ["benchmark_test.py"]
        assert "/" not in result[0]

    def test_ignores_subdirectories(self):
        tmpdir = tempfile.mkdtemp()
        subdir = Path(tmpdir, "benchmark_subdir")
        subdir.mkdir()
        Path(tmpdir, "benchmark_script.py").write_text("# ok")
        result = _discover_scripts(tmpdir)
        assert result == ["benchmark_script.py"]


# --- GovernanceReport ---

class TestGovernanceReport:
    def test_is_dataclass(self):
        report = GovernanceReport(total_scripts=0)
        assert isinstance(report, GovernanceReport)

    def test_default_is_compliant_true(self):
        report = GovernanceReport(total_scripts=0)
        assert report.is_compliant is True

    def test_default_empty_lists(self):
        report = GovernanceReport(total_scripts=0)
        assert report.governed_scripts == []
        assert report.ungoverned_scripts == []
        assert report.compliant_scripts == []
        assert report.violations == []

    def test_default_empty_summary(self):
        report = GovernanceReport(total_scripts=0)
        assert report.violation_summary == ""


# --- check_governance ---

class TestCheckGovernance:
    def test_empty_dir_is_compliant(self):
        tmpdir = tempfile.mkdtemp()
        registry = _make_registry("BMC-0001")
        report = check_governance(tmpdir, registry)
        assert report.is_compliant is True
        assert report.total_scripts == 0

    def test_only_ungoverned_scripts_is_compliant(self):
        tmpdir = _make_scripts_dir(["benchmark_unknown.py"])
        registry = _make_registry("BMC-0001")
        report = check_governance(tmpdir, registry)
        assert report.is_compliant is True
        assert report.ungoverned_scripts == ["benchmark_unknown.py"]
        assert report.violations == []

    def test_governed_script_with_valid_card_is_compliant(self):
        tmpdir = _make_scripts_dir(["benchmark_precision_at_k.py"])
        registry = _make_registry("BMC-0001")
        report = check_governance(tmpdir, registry)
        assert report.is_compliant is True
        assert "benchmark_precision_at_k.py" in report.compliant_scripts
        assert report.violations == []

    def test_governed_script_missing_card_is_violation(self):
        tmpdir = _make_scripts_dir(["benchmark_precision_at_k.py"])
        registry = {}  # empty registry
        report = check_governance(tmpdir, registry)
        assert report.is_compliant is False
        assert len(report.violations) == 1
        assert "BMC-0001" in report.violations[0]

    def test_violation_summary_contains_fail(self):
        tmpdir = _make_scripts_dir(["benchmark_precision_at_k.py"])
        registry = {}
        report = check_governance(tmpdir, registry)
        assert "FAIL" in report.violation_summary or "violation" in report.violation_summary.lower()

    def test_compliant_summary_contains_ok(self):
        tmpdir = _make_scripts_dir(["benchmark_precision_at_k.py"])
        registry = _make_registry("BMC-0001")
        report = check_governance(tmpdir, registry)
        assert report.is_compliant is True
        assert "OK" in report.violation_summary or "ok" in report.violation_summary.lower()

    def test_total_scripts_counts_all_discovered(self):
        tmpdir = _make_scripts_dir([
            "benchmark_precision_at_k.py",
            "benchmark_unknown_extra.py",
        ])
        registry = _make_registry("BMC-0001")
        report = check_governance(tmpdir, registry)
        assert report.total_scripts == 2

    def test_governed_list_contains_only_governed(self):
        tmpdir = _make_scripts_dir([
            "benchmark_precision_at_k.py",
            "benchmark_unknown.py",
        ])
        registry = _make_registry("BMC-0001")
        report = check_governance(tmpdir, registry)
        assert report.governed_scripts == ["benchmark_precision_at_k.py"]

    def test_ungoverned_list_contains_only_ungoverned(self):
        tmpdir = _make_scripts_dir([
            "benchmark_precision_at_k.py",
            "benchmark_unknown.py",
        ])
        registry = _make_registry("BMC-0001")
        report = check_governance(tmpdir, registry)
        assert report.ungoverned_scripts == ["benchmark_unknown.py"]

    def test_multiple_governed_all_compliant(self):
        tmpdir = _make_scripts_dir([
            "benchmark_precision_at_k.py",
            "benchmark_charge_matched.py",
        ])
        registry = _make_registry("BMC-0001", "BMC-0002")
        report = check_governance(tmpdir, registry)
        assert report.is_compliant is True
        assert len(report.compliant_scripts) == 2

    def test_multiple_governed_one_missing_card(self):
        tmpdir = _make_scripts_dir([
            "benchmark_precision_at_k.py",
            "benchmark_charge_matched.py",
        ])
        registry = _make_registry("BMC-0001")  # BMC-0002 missing
        report = check_governance(tmpdir, registry)
        assert report.is_compliant is False
        assert len(report.violations) == 1

    def test_custom_governed_scripts(self):
        custom_governed = frozenset({"benchmark_custom.py"})
        custom_mapping = {"benchmark_custom.py": "BMC-9999"}
        tmpdir = _make_scripts_dir(["benchmark_custom.py"])
        registry = _make_registry("BMC-9999")
        report = check_governance(
            tmpdir, registry,
            governed_scripts=custom_governed,
            script_to_bmc_id=custom_mapping,
        )
        assert report.is_compliant is True
        assert "benchmark_custom.py" in report.compliant_scripts

    def test_custom_governed_missing_card(self):
        custom_governed = frozenset({"benchmark_custom.py"})
        custom_mapping = {"benchmark_custom.py": "BMC-9999"}
        tmpdir = _make_scripts_dir(["benchmark_custom.py"])
        registry = {}
        report = check_governance(
            tmpdir, registry,
            governed_scripts=custom_governed,
            script_to_bmc_id=custom_mapping,
        )
        assert report.is_compliant is False

    def test_governed_script_in_mapping_but_no_bmc_entry(self):
        # Script is governed but mapping is missing its BMC ID key
        custom_governed = frozenset({"benchmark_special.py"})
        custom_mapping = {}  # mapping doesn't have benchmark_special.py
        tmpdir = _make_scripts_dir(["benchmark_special.py"])
        registry = {}
        report = check_governance(
            tmpdir, registry,
            governed_scripts=custom_governed,
            script_to_bmc_id=custom_mapping,
        )
        assert report.is_compliant is False
        assert any("SCRIPT_TO_BMC_ID" in v for v in report.violations)

    def test_returns_governance_report_type(self):
        tmpdir = tempfile.mkdtemp()
        report = check_governance(tmpdir, {})
        assert isinstance(report, GovernanceReport)

    def test_all_five_governed_scripts_compliant(self):
        tmpdir = _make_scripts_dir(list(GOVERNED_SCRIPTS))
        registry = _make_registry("BMC-0001", "BMC-0002", "BMC-0003", "BMC-0004", "BMC-0005")
        report = check_governance(tmpdir, registry)
        assert report.is_compliant is True
        assert len(report.compliant_scripts) == 5
        assert report.violations == []

    def test_violation_count_in_summary(self):
        tmpdir = _make_scripts_dir([
            "benchmark_precision_at_k.py",
            "benchmark_charge_matched.py",
        ])
        registry = {}  # both missing
        report = check_governance(tmpdir, registry)
        assert len(report.violations) == 2


# --- format_governance_report ---

class TestFormatGovernanceReport:
    def _compliant_report(self) -> GovernanceReport:
        tmpdir = _make_scripts_dir(["benchmark_precision_at_k.py"])
        registry = _make_registry("BMC-0001")
        return check_governance(tmpdir, registry)

    def _violation_report(self) -> GovernanceReport:
        tmpdir = _make_scripts_dir(["benchmark_precision_at_k.py"])
        registry = {}
        return check_governance(tmpdir, registry)

    def test_returns_string(self):
        assert isinstance(format_governance_report(self._compliant_report()), str)

    def test_contains_header(self):
        text = format_governance_report(self._compliant_report())
        assert "BENCHMARK GOVERNANCE REPORT" in text

    def test_contains_scripts_discovered(self):
        text = format_governance_report(self._compliant_report())
        assert "Scripts discovered" in text

    def test_contains_compliant_count(self):
        text = format_governance_report(self._compliant_report())
        assert "COMPLIANT" in text

    def test_compliant_shows_pass(self):
        text = format_governance_report(self._compliant_report())
        assert "PASS" in text

    def test_violation_shows_fail(self):
        text = format_governance_report(self._violation_report())
        assert "FAIL" in text

    def test_violation_shows_script_name(self):
        text = format_governance_report(self._violation_report())
        assert "benchmark_precision_at_k.py" in text

    def test_ungoverned_section_present_when_ungoverned(self):
        tmpdir = _make_scripts_dir(["benchmark_ungoverned_x.py"])
        registry = {}
        report = check_governance(tmpdir, registry)
        text = format_governance_report(report)
        assert "UNGOVERNED" in text

    def test_no_ungoverned_section_when_none(self):
        tmpdir = _make_scripts_dir(["benchmark_precision_at_k.py"])
        registry = _make_registry("BMC-0001")
        report = check_governance(tmpdir, registry)
        text = format_governance_report(report)
        # No ungoverned scripts means the section should not appear
        assert "ungoverned_x" not in text

    def test_violation_summary_in_output(self):
        report = self._violation_report()
        text = format_governance_report(report)
        assert report.violation_summary in text

    def test_empty_report_does_not_crash(self):
        report = GovernanceReport(total_scripts=0)
        text = format_governance_report(report)
        assert isinstance(text, str)
        assert len(text) > 0
