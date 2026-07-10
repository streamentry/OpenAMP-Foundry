"""Tests for benchmark card registry — Phase C C1.

63 tests verifying that the benchmark registry contains valid BMC- cards
for all major pipeline benchmarks, making governance machine-enforceable.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.benchmark_card import (
    VALID_EVALUATION_METRICS,
    VALID_MEASUREMENT_TARGETS,
    VALID_SPLIT_STRATEGIES,
    BenchmarkCard,
)
from openamp_foundry.evidence.benchmark_registry import (
    BENCHMARK_REGISTRY,
    BENCHMARK_REGISTRY_BY_ID,
    get_card,
    validate_registry,
)


# ---------------------------------------------------------------------------
# Group 1: RegistryStructure (8 tests)
# ---------------------------------------------------------------------------

class TestRegistryStructure:
    def test_registry_is_list(self):
        assert isinstance(BENCHMARK_REGISTRY, list)

    def test_registry_non_empty(self):
        assert len(BENCHMARK_REGISTRY) >= 5

    def test_registry_by_id_is_dict(self):
        assert isinstance(BENCHMARK_REGISTRY_BY_ID, dict)

    def test_registry_by_id_same_length(self):
        assert len(BENCHMARK_REGISTRY_BY_ID) == len(BENCHMARK_REGISTRY)

    def test_all_registry_entries_are_benchmark_cards(self):
        for card in BENCHMARK_REGISTRY:
            assert isinstance(card, BenchmarkCard)

    def test_get_card_function_exists(self):
        assert callable(get_card)

    def test_validate_registry_function_exists(self):
        assert callable(validate_registry)

    def test_registry_ids_unique(self):
        ids = [card.bmc_id for card in BENCHMARK_REGISTRY]
        assert len(ids) == len(set(ids)), "BMC IDs must be unique"


# ---------------------------------------------------------------------------
# Group 2: AllCardsValid (8 tests)
# ---------------------------------------------------------------------------

class TestAllCardsValid:
    def test_validate_registry_returns_no_errors(self):
        errors = validate_registry()
        assert errors == [], f"Registry has validation errors:\n" + "\n".join(errors)

    def test_each_card_validates_individually(self):
        for card in BENCHMARK_REGISTRY:
            hard_errors = [e for e in card.validate() if not e.startswith("WARNING")]
            assert hard_errors == [], f"{card.bmc_id} has errors: {hard_errors}"

    def test_all_bmc_ids_have_correct_prefix(self):
        for card in BENCHMARK_REGISTRY:
            assert card.bmc_id.startswith("BMC-"), f"{card.bmc_id!r} missing BMC- prefix"

    def test_all_cards_have_pipeline_version(self):
        for card in BENCHMARK_REGISTRY:
            assert card.pipeline_version.strip(), f"{card.bmc_id} missing pipeline_version"

    def test_all_cards_have_benchmark_name(self):
        for card in BENCHMARK_REGISTRY:
            assert card.benchmark_name.strip(), f"{card.bmc_id} missing benchmark_name"

    def test_all_cards_have_valid_measurement_target(self):
        for card in BENCHMARK_REGISTRY:
            assert card.measurement_target in VALID_MEASUREMENT_TARGETS, (
                f"{card.bmc_id}: measurement_target {card.measurement_target!r} not in vocab"
            )

    def test_all_cards_have_valid_split_strategy(self):
        for card in BENCHMARK_REGISTRY:
            assert card.split_strategy in VALID_SPLIT_STRATEGIES, (
                f"{card.bmc_id}: split_strategy {card.split_strategy!r} not in vocab"
            )

    def test_all_cards_have_valid_evaluation_metrics(self):
        for card in BENCHMARK_REGISTRY:
            for metric in card.evaluation_metrics:
                assert metric in VALID_EVALUATION_METRICS, (
                    f"{card.bmc_id}: metric {metric!r} not in vocab"
                )


# ---------------------------------------------------------------------------
# Group 3: CheapEnemyRequirements (10 tests)
# ---------------------------------------------------------------------------

class TestCheapEnemyRequirements:
    def test_all_cards_have_cheap_enemies(self):
        for card in BENCHMARK_REGISTRY:
            assert len(card.cheap_enemy_baselines) >= 1, (
                f"{card.bmc_id} has no cheap enemy baselines"
            )

    def test_all_cheap_enemies_non_empty(self):
        for card in BENCHMARK_REGISTRY:
            for enemy in card.cheap_enemy_baselines:
                assert enemy.strip(), f"{card.bmc_id}: empty cheap enemy string"

    def test_most_cards_have_two_or_more_cheap_enemies(self):
        cards_with_two_plus = [
            card for card in BENCHMARK_REGISTRY
            if len(card.cheap_enemy_baselines) >= 2
        ]
        # At least 3 out of 5 cards should have 2+ cheap enemies
        assert len(cards_with_two_plus) >= 3

    def test_bmc0001_has_charge_enemy(self):
        card = get_card("BMC-0001")
        assert card is not None
        assert any("charge" in e.lower() for e in card.cheap_enemy_baselines)

    def test_bmc0001_has_length_enemy(self):
        card = get_card("BMC-0001")
        assert card is not None
        assert any("length" in e.lower() for e in card.cheap_enemy_baselines)

    def test_bmc0005_has_most_cheap_enemies(self):
        card = get_card("BMC-0005")
        assert card is not None
        assert len(card.cheap_enemy_baselines) >= 3

    def test_cheap_enemy_comparison_benchmark_has_conjunction_enemy(self):
        card = get_card("BMC-0005")
        assert card is not None
        assert any("conjunction" in e.lower() for e in card.cheap_enemy_baselines)

    def test_calibration_benchmark_has_isotonic_enemy(self):
        card = get_card("BMC-0003")
        assert card is not None
        assert any("isotonic" in e.lower() or "recalib" in e.lower() for e in card.cheap_enemy_baselines)

    def test_all_cheap_enemy_strings_are_descriptive(self):
        for card in BENCHMARK_REGISTRY:
            for enemy in card.cheap_enemy_baselines:
                assert len(enemy) >= 5, (
                    f"{card.bmc_id}: cheap enemy {enemy!r} is too short to be descriptive"
                )

    def test_charge_matched_benchmark_has_charge_enemy(self):
        card = get_card("BMC-0002")
        assert card is not None
        assert any("charge" in e.lower() for e in card.cheap_enemy_baselines)


# ---------------------------------------------------------------------------
# Group 4: KnownLimitationsRequirements (8 tests)
# ---------------------------------------------------------------------------

class TestKnownLimitationsRequirements:
    def test_all_cards_have_known_limitations(self):
        for card in BENCHMARK_REGISTRY:
            assert len(card.known_limitations) >= 1, (
                f"{card.bmc_id} has no known_limitations"
            )

    def test_all_limitations_non_empty(self):
        for card in BENCHMARK_REGISTRY:
            for lim in card.known_limitations:
                assert lim.strip(), f"{card.bmc_id}: empty limitation string"

    def test_most_cards_have_two_or_more_limitations(self):
        cards_with_two_plus = [
            card for card in BENCHMARK_REGISTRY
            if len(card.known_limitations) >= 2
        ]
        assert len(cards_with_two_plus) >= 3

    def test_bmc0001_has_training_data_limitation(self):
        card = get_card("BMC-0001")
        assert card is not None
        combined = " ".join(card.known_limitations).lower()
        assert "apd" in combined or "train" in combined or "data" in combined

    def test_calibration_benchmark_limitation_mentions_domain(self):
        card = get_card("BMC-0003")
        assert card is not None
        combined = " ".join(card.known_limitations).lower()
        assert "domain" in combined or "scaffold" in combined or "transfer" in combined

    def test_family_benchmark_limitation_mentions_family(self):
        card = get_card("BMC-0004")
        assert card is not None
        combined = " ".join(card.known_limitations).lower()
        assert "family" in combined or "label" in combined

    def test_all_limitations_descriptive(self):
        for card in BENCHMARK_REGISTRY:
            for lim in card.known_limitations:
                assert len(lim) >= 10, (
                    f"{card.bmc_id}: limitation {lim!r} too short"
                )

    def test_cheap_enemy_comparison_limitation_mentions_heuristic(self):
        card = get_card("BMC-0005")
        assert card is not None
        combined = " ".join(card.known_limitations).lower()
        assert "heuristic" in combined or "fixed" in combined or "threshold" in combined


# ---------------------------------------------------------------------------
# Group 5: GetCardFunction (8 tests)
# ---------------------------------------------------------------------------

class TestGetCardFunction:
    def test_get_card_bmc0001(self):
        card = get_card("BMC-0001")
        assert card is not None
        assert card.bmc_id == "BMC-0001"

    def test_get_card_bmc0002(self):
        card = get_card("BMC-0002")
        assert card is not None
        assert card.bmc_id == "BMC-0002"

    def test_get_card_bmc0003(self):
        card = get_card("BMC-0003")
        assert card is not None
        assert card.bmc_id == "BMC-0003"

    def test_get_card_bmc0004(self):
        card = get_card("BMC-0004")
        assert card is not None
        assert card.bmc_id == "BMC-0004"

    def test_get_card_bmc0005(self):
        card = get_card("BMC-0005")
        assert card is not None
        assert card.bmc_id == "BMC-0005"

    def test_get_card_nonexistent_returns_none(self):
        assert get_card("BMC-9999") is None

    def test_get_card_empty_string_returns_none(self):
        assert get_card("") is None

    def test_get_card_wrong_prefix_returns_none(self):
        assert get_card("BMC0001") is None


# ---------------------------------------------------------------------------
# Group 6: BenchmarkTypesCovered (10 tests)
# ---------------------------------------------------------------------------

class TestBenchmarkTypesCovered:
    def test_has_activity_prediction_benchmark(self):
        targets = {card.measurement_target for card in BENCHMARK_REGISTRY}
        assert "antimicrobial_activity_prediction" in targets

    def test_has_calibration_benchmark(self):
        targets = {card.measurement_target for card in BENCHMARK_REGISTRY}
        assert "calibration_accuracy" in targets

    def test_has_ensemble_ranking_benchmark(self):
        targets = {card.measurement_target for card in BENCHMARK_REGISTRY}
        assert "ensemble_ranking" in targets

    def test_has_leakage_aware_split(self):
        strategies = {card.split_strategy for card in BENCHMARK_REGISTRY}
        assert "leakage_aware_split" in strategies

    def test_has_family_stratified_split(self):
        strategies = {card.split_strategy for card in BENCHMARK_REGISTRY}
        assert "family_stratified" in strategies

    def test_has_charge_stratified_split(self):
        strategies = {card.split_strategy for card in BENCHMARK_REGISTRY}
        assert "charge_stratified" in strategies

    def test_has_precision_at_k_metric(self):
        all_metrics = {m for card in BENCHMARK_REGISTRY for m in card.evaluation_metrics}
        assert "precision_at_k" in all_metrics

    def test_has_calibration_error_metric(self):
        all_metrics = {m for card in BENCHMARK_REGISTRY for m in card.evaluation_metrics}
        assert "calibration_error" in all_metrics

    def test_no_deprecated_cards_in_initial_registry(self):
        deprecated = [card for card in BENCHMARK_REGISTRY if card.deprecated]
        assert len(deprecated) == 0

    def test_all_cards_have_created_date(self):
        for card in BENCHMARK_REGISTRY:
            assert card.created_date.strip()


# ---------------------------------------------------------------------------
# Group 7: RegistryByIDAndNotes (11 tests)
# ---------------------------------------------------------------------------

class TestRegistryByIDAndNotes:
    def test_registry_by_id_keys_are_bmc_ids(self):
        for bmc_id in BENCHMARK_REGISTRY_BY_ID:
            assert bmc_id.startswith("BMC-")

    def test_registry_by_id_values_are_cards(self):
        for card in BENCHMARK_REGISTRY_BY_ID.values():
            assert isinstance(card, BenchmarkCard)

    def test_registry_by_id_lookup_consistent(self):
        for card in BENCHMARK_REGISTRY:
            assert BENCHMARK_REGISTRY_BY_ID[card.bmc_id] is card

    def test_bmc0001_notes_non_empty(self):
        card = get_card("BMC-0001")
        assert card is not None
        assert card.notes.strip()

    def test_bmc0005_notes_mention_anti_hype(self):
        card = get_card("BMC-0005")
        assert card is not None
        assert "anti" in card.notes.lower() or "enemy" in card.notes.lower() or "ranking authority" in card.notes.lower()

    def test_bmc0003_notes_mention_release(self):
        card = get_card("BMC-0003")
        assert card is not None
        assert "release" in card.notes.lower() or "calibration" in card.notes.lower()

    def test_all_cards_notes_at_most_500_chars(self):
        for card in BENCHMARK_REGISTRY:
            assert len(card.notes) <= 500, f"{card.bmc_id} notes too long"

    def test_bmc0001_evaluation_metrics_includes_enrichment(self):
        card = get_card("BMC-0001")
        assert card is not None
        assert "enrichment_factor" in card.evaluation_metrics

    def test_bmc0004_has_recall_at_k(self):
        card = get_card("BMC-0004")
        assert card is not None
        assert "recall_at_k" in card.evaluation_metrics

    def test_validate_registry_returns_list(self):
        assert isinstance(validate_registry(), list)

    def test_bmc0002_notes_references_bmc0003(self):
        card = get_card("BMC-0002")
        assert card is not None
        # Notes should reference the next benchmark for combined control
        assert "BMC-0003" in card.notes or "combined" in card.notes.lower() or "charge" in card.notes.lower()
