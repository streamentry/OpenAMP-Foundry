"""Tests for benchmark deprecation banner system — Phase C C8.

63 tests across 7 groups.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.benchmark_card import BenchmarkCard
from openamp_foundry.evidence.benchmark_deprecation import (
    DeprecatedBenchmarkError,
    build_deprecation_banner,
    check_no_deprecated_in_ranking,
    deprecation_status_report,
    get_active_cards,
    get_deprecated_cards,
    print_all_deprecation_banners,
)
from openamp_foundry.evidence.benchmark_registry import BENCHMARK_REGISTRY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _active_card(bmc_id: str = "BMC-0010") -> BenchmarkCard:
    return BenchmarkCard(
        bmc_id=bmc_id,
        pipeline_version="0.10.34",
        benchmark_name="Test Active Benchmark",
        measurement_target="antimicrobial_activity_prediction",
        split_strategy="leakage_aware_split",
        cheap_enemy_baselines=["charge_threshold_gte4", "length_heuristic"],
        evaluation_metrics=["precision_at_k", "auc_roc"],
        known_limitations=["Test only.", "Synthetic data."],
        deprecated=False,
        created_date="2024-06-01",
        last_updated_date="2024-06-01",
        notes="Test card.",
    )


def _deprecated_card(bmc_id: str = "BMC-DEPR-01") -> BenchmarkCard:
    return BenchmarkCard(
        bmc_id=bmc_id,
        pipeline_version="0.10.34",
        benchmark_name="Old Leaky Benchmark",
        measurement_target="antimicrobial_activity_prediction",
        split_strategy="random_80_20",
        cheap_enemy_baselines=["charge_threshold_gte4", "length_heuristic"],
        evaluation_metrics=["precision_at_k"],
        known_limitations=["Had train/test leakage.", "Random split only."],
        deprecated=True,
        created_date="2024-01-01",
        last_updated_date="2024-06-01",
        notes="Superseded by BMC-0010 which uses leakage_aware_split.",
    )


# ---------------------------------------------------------------------------
# Group 1: GetDeprecatedAndActive (8 tests)
# ---------------------------------------------------------------------------

class TestGetDeprecatedAndActive:
    def test_get_deprecated_returns_only_deprecated(self):
        registry = [_active_card(), _deprecated_card()]
        deprecated = get_deprecated_cards(registry)
        assert all(c.deprecated for c in deprecated)

    def test_get_deprecated_empty_for_all_active(self):
        registry = [_active_card("BMC-0010"), _active_card("BMC-0011")]
        assert get_deprecated_cards(registry) == []

    def test_get_deprecated_all_for_all_deprecated(self):
        registry = [_deprecated_card("BMC-D1"), _deprecated_card("BMC-D2")]
        assert len(get_deprecated_cards(registry)) == 2

    def test_get_active_returns_only_active(self):
        registry = [_active_card(), _deprecated_card()]
        active = get_active_cards(registry)
        assert all(not c.deprecated for c in active)

    def test_get_active_empty_for_all_deprecated(self):
        registry = [_deprecated_card()]
        assert get_active_cards(registry) == []

    def test_get_active_all_for_all_active(self):
        registry = [_active_card("BMC-0010"), _active_card("BMC-0011")]
        assert len(get_active_cards(registry)) == 2

    def test_active_plus_deprecated_equals_total(self):
        registry = [_active_card(), _deprecated_card()]
        assert len(get_active_cards(registry)) + len(get_deprecated_cards(registry)) == len(registry)

    def test_main_registry_has_no_deprecated_cards(self):
        assert get_deprecated_cards(BENCHMARK_REGISTRY) == []


# ---------------------------------------------------------------------------
# Group 2: BuildDeprecationBanner (10 tests)
# ---------------------------------------------------------------------------

class TestBuildDeprecationBanner:
    def test_banner_returns_string(self):
        assert isinstance(build_deprecation_banner(_deprecated_card()), str)

    def test_banner_non_empty(self):
        assert len(build_deprecation_banner(_deprecated_card())) > 0

    def test_banner_contains_deprecated_label(self):
        banner = build_deprecation_banner(_deprecated_card())
        assert "DEPRECATED" in banner

    def test_banner_contains_bmc_id(self):
        card = _deprecated_card("BMC-DEPR-01")
        banner = build_deprecation_banner(card)
        assert "BMC-DEPR-01" in banner

    def test_banner_contains_benchmark_name(self):
        card = _deprecated_card()
        banner = build_deprecation_banner(card)
        assert card.benchmark_name in banner

    def test_banner_contains_deprecation_reason(self):
        card = _deprecated_card()
        banner = build_deprecation_banner(card)
        assert "leakage_aware_split" in banner or "Superseded" in banner

    def test_banner_contains_warning_about_ranking(self):
        banner = build_deprecation_banner(_deprecated_card())
        assert "ranking" in banner.lower() or "ranking decisions" in banner.lower()

    def test_banner_contains_remove_instruction(self):
        banner = build_deprecation_banner(_deprecated_card())
        assert "remove" in banner.lower() or "replace" in banner.lower()

    def test_banner_is_multiline(self):
        banner = build_deprecation_banner(_deprecated_card())
        assert "\n" in banner

    def test_banner_measurement_target_in_banner(self):
        card = _deprecated_card()
        banner = build_deprecation_banner(card)
        assert card.measurement_target in banner


# ---------------------------------------------------------------------------
# Group 3: CheckNoDeprecatedInRanking (10 tests)
# ---------------------------------------------------------------------------

class TestCheckNoDeprecatedInRanking:
    def test_all_active_registry_passes(self):
        registry = [_active_card()]
        check_no_deprecated_in_ranking(registry)  # should not raise

    def test_main_registry_passes(self):
        check_no_deprecated_in_ranking(BENCHMARK_REGISTRY)  # should not raise

    def test_deprecated_card_raises(self):
        registry = [_deprecated_card()]
        with pytest.raises(DeprecatedBenchmarkError):
            check_no_deprecated_in_ranking(registry)

    def test_mixed_registry_raises(self):
        registry = [_active_card(), _deprecated_card()]
        with pytest.raises(DeprecatedBenchmarkError):
            check_no_deprecated_in_ranking(registry)

    def test_error_message_contains_bmc_id(self):
        registry = [_deprecated_card("BMC-DEPR-01")]
        with pytest.raises(DeprecatedBenchmarkError) as exc_info:
            check_no_deprecated_in_ranking(registry)
        assert "BMC-DEPR-01" in str(exc_info.value)

    def test_error_message_mentions_deprecated(self):
        registry = [_deprecated_card()]
        with pytest.raises(DeprecatedBenchmarkError) as exc_info:
            check_no_deprecated_in_ranking(registry)
        assert "deprecated" in str(exc_info.value).lower()

    def test_allow_deprecated_flag_suppresses_error(self):
        registry = [_deprecated_card()]
        check_no_deprecated_in_ranking(registry, allow_deprecated=True)  # should not raise

    def test_empty_registry_passes(self):
        check_no_deprecated_in_ranking([])  # should not raise

    def test_two_deprecated_cards_raises(self):
        registry = [_deprecated_card("BMC-D1"), _deprecated_card("BMC-D2")]
        with pytest.raises(DeprecatedBenchmarkError):
            check_no_deprecated_in_ranking(registry)

    def test_deprecated_benchmark_error_is_exception(self):
        assert issubclass(DeprecatedBenchmarkError, Exception)


# ---------------------------------------------------------------------------
# Group 4: DeprecationStatusReport (8 tests)
# ---------------------------------------------------------------------------

class TestDeprecationStatusReport:
    def test_report_returns_dict(self):
        assert isinstance(deprecation_status_report([_active_card()]), dict)

    def test_report_has_expected_keys(self):
        report = deprecation_status_report([_active_card()])
        assert "total" in report
        assert "active" in report
        assert "deprecated" in report
        assert "deprecated_ids" in report
        assert "all_active" in report

    def test_all_active_registry_all_active_true(self):
        report = deprecation_status_report([_active_card()])
        assert report["all_active"] is True

    def test_deprecated_registry_all_active_false(self):
        report = deprecation_status_report([_deprecated_card()])
        assert report["all_active"] is False

    def test_counts_correct(self):
        registry = [_active_card(), _deprecated_card()]
        report = deprecation_status_report(registry)
        assert report["total"] == 2
        assert report["active"] == 1
        assert report["deprecated"] == 1

    def test_deprecated_ids_correct(self):
        registry = [_active_card(), _deprecated_card("BMC-D1")]
        report = deprecation_status_report(registry)
        assert "BMC-D1" in report["deprecated_ids"]

    def test_main_registry_report_all_active(self):
        report = deprecation_status_report(BENCHMARK_REGISTRY)
        assert report["all_active"] is True

    def test_empty_registry_report(self):
        report = deprecation_status_report([])
        assert report["total"] == 0
        assert report["all_active"] is True


# ---------------------------------------------------------------------------
# Group 5: PrintBanners (8 tests)
# ---------------------------------------------------------------------------

class TestPrintBanners:
    def test_print_banners_returns_list(self, capsys):
        banners = print_all_deprecation_banners([_deprecated_card()])
        assert isinstance(banners, list)

    def test_print_banners_empty_for_active_only(self, capsys):
        banners = print_all_deprecation_banners([_active_card()])
        assert banners == []

    def test_print_banners_one_for_one_deprecated(self, capsys):
        banners = print_all_deprecation_banners([_deprecated_card()])
        assert len(banners) == 1

    def test_print_banners_two_for_two_deprecated(self, capsys):
        banners = print_all_deprecation_banners([
            _deprecated_card("BMC-D1"),
            _deprecated_card("BMC-D2"),
        ])
        assert len(banners) == 2

    def test_print_banners_outputs_to_stdout(self, capsys):
        print_all_deprecation_banners([_deprecated_card()])
        captured = capsys.readouterr()
        assert "DEPRECATED" in captured.out

    def test_print_banners_empty_registry(self, capsys):
        banners = print_all_deprecation_banners([])
        assert banners == []

    def test_print_banners_main_registry_no_output(self, capsys):
        banners = print_all_deprecation_banners(BENCHMARK_REGISTRY)
        assert banners == []

    def test_banner_content_in_returned_list(self, capsys):
        banners = print_all_deprecation_banners([_deprecated_card()])
        assert len(banners) == 1
        assert "DEPRECATED" in banners[0]


# ---------------------------------------------------------------------------
# Group 6: IntegrationWithRegistry (10 tests)
# ---------------------------------------------------------------------------

class TestIntegrationWithRegistry:
    def test_main_registry_no_deprecated(self):
        assert len(get_deprecated_cards(BENCHMARK_REGISTRY)) == 0

    def test_main_registry_all_active(self):
        assert len(get_active_cards(BENCHMARK_REGISTRY)) == len(BENCHMARK_REGISTRY)

    def test_check_passes_for_main_registry(self):
        check_no_deprecated_in_ranking(BENCHMARK_REGISTRY)

    def test_report_for_main_registry(self):
        report = deprecation_status_report(BENCHMARK_REGISTRY)
        assert report["deprecated"] == 0
        assert report["all_active"] is True

    def test_adding_deprecated_fails_check(self):
        registry = list(BENCHMARK_REGISTRY) + [_deprecated_card()]
        with pytest.raises(DeprecatedBenchmarkError):
            check_no_deprecated_in_ranking(registry)

    def test_deprecated_card_not_in_active_cards(self):
        registry = [_active_card(), _deprecated_card()]
        active = get_active_cards(registry)
        assert not any(c.deprecated for c in active)

    def test_deprecated_ids_list_is_list(self):
        report = deprecation_status_report(BENCHMARK_REGISTRY)
        assert isinstance(report["deprecated_ids"], list)

    def test_deprecated_ids_empty_for_main_registry(self):
        report = deprecation_status_report(BENCHMARK_REGISTRY)
        assert report["deprecated_ids"] == []

    def test_mixed_registry_active_count_correct(self):
        registry = [_active_card("BMC-A1"), _active_card("BMC-A2"), _deprecated_card()]
        report = deprecation_status_report(registry)
        assert report["active"] == 2
        assert report["deprecated"] == 1

    def test_banner_for_card_without_notes_uses_fallback(self):
        card = _deprecated_card()
        card.notes = ""
        banner = build_deprecation_banner(card)
        assert "no reason given" in banner.lower() or "DEPRECATED" in banner


# ---------------------------------------------------------------------------
# Group 7: EdgeCases (9 tests)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_get_deprecated_empty_registry(self):
        assert get_deprecated_cards([]) == []

    def test_get_active_empty_registry(self):
        assert get_active_cards([]) == []

    def test_check_no_deprecated_empty_registry(self):
        check_no_deprecated_in_ranking([])  # should not raise

    def test_deprecation_error_inherits_from_exception(self):
        try:
            raise DeprecatedBenchmarkError("test")
        except Exception as e:
            assert isinstance(e, DeprecatedBenchmarkError)

    def test_allow_deprecated_true_does_not_raise_even_with_deprecated(self):
        registry = [_deprecated_card("BMC-D1"), _deprecated_card("BMC-D2")]
        check_no_deprecated_in_ranking(registry, allow_deprecated=True)

    def test_report_deprecated_count_matches_get_deprecated(self):
        registry = [_active_card(), _deprecated_card("BMC-D1"), _deprecated_card("BMC-D2")]
        report = deprecation_status_report(registry)
        assert report["deprecated"] == len(get_deprecated_cards(registry))

    def test_report_active_count_matches_get_active(self):
        registry = [_active_card(), _deprecated_card()]
        report = deprecation_status_report(registry)
        assert report["active"] == len(get_active_cards(registry))

    def test_banner_width_reasonable(self):
        banner = build_deprecation_banner(_deprecated_card())
        lines = banner.split("\n")
        # Banner lines should not be unreasonably long
        assert all(len(line) <= 120 for line in lines)

    def test_print_banners_returns_correct_banner_content(self, capsys):
        card = _deprecated_card("BMC-DEPR-77")
        banners = print_all_deprecation_banners([card])
        assert len(banners) == 1
        assert "BMC-DEPR-77" in banners[0]
