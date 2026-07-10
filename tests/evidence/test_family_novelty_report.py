import pytest
from src.openamp_foundry.evidence.family_novelty_report import (
    VALID_BASELINE_COMPARISON_OUTCOMES,
    VALID_NOVELTY_STRENGTH_GRADES,
    VALID_CHEAP_BASELINES_CHECKED,
    FamilyNoveltyReport,
    FNRValidationResult,
    validate_family_novelty_report,
    build_family_novelty_report,
    format_family_novelty_report,
)


def _valid_report(**kwargs):
    defaults = dict(
        fnr_id="FNR-0001",
        cfc_id="CFC-0001",
        family_name="Alpha-Helix Family 1",
        cheap_baselines_checked=["charge_distribution", "length_distribution"],
        baseline_comparison_outcome="outside_known_space",
        novelty_strength_grade="strong",
        n_known_families_compared=5,
        known_families_compared=["defensin_family", "cathelicidin_family"],
        cheap_enemy_score=0.42,
        family_score=0.87,
        dry_lab_only=True,
        limitations="Limited to gram-positive AMP databases; gram-negative families not compared.",
        notes="",
    )
    defaults.update(kwargs)
    return FamilyNoveltyReport(**defaults)


# ── Constants ──────────────────────────────────────────────────────────────────

class TestConstants:
    def test_baseline_comparison_outcomes_is_frozenset(self):
        assert isinstance(VALID_BASELINE_COMPARISON_OUTCOMES, frozenset)

    def test_baseline_comparison_outcomes_count(self):
        assert len(VALID_BASELINE_COMPARISON_OUTCOMES) == 4

    def test_outside_known_space_in_outcomes(self):
        assert "outside_known_space" in VALID_BASELINE_COMPARISON_OUTCOMES

    def test_within_known_space_in_outcomes(self):
        assert "within_known_space" in VALID_BASELINE_COMPARISON_OUTCOMES

    def test_comparison_not_run_in_outcomes(self):
        assert "comparison_not_run" in VALID_BASELINE_COMPARISON_OUTCOMES

    def test_novelty_strength_grades_is_frozenset(self):
        assert isinstance(VALID_NOVELTY_STRENGTH_GRADES, frozenset)

    def test_novelty_strength_grades_count(self):
        assert len(VALID_NOVELTY_STRENGTH_GRADES) == 4

    def test_strong_in_grades(self):
        assert "strong" in VALID_NOVELTY_STRENGTH_GRADES

    def test_not_supported_in_grades(self):
        assert "not_supported" in VALID_NOVELTY_STRENGTH_GRADES

    def test_cheap_baselines_is_frozenset(self):
        assert isinstance(VALID_CHEAP_BASELINES_CHECKED, frozenset)

    def test_cheap_baselines_count(self):
        assert len(VALID_CHEAP_BASELINES_CHECKED) == 5

    def test_charge_distribution_in_baselines(self):
        assert "charge_distribution" in VALID_CHEAP_BASELINES_CHECKED

    def test_hydrophobicity_profile_in_baselines(self):
        assert "hydrophobicity_profile" in VALID_CHEAP_BASELINES_CHECKED


# ── Dataclass ──────────────────────────────────────────────────────────────────

class TestFamilyNoveltyReportDataclass:
    def test_instantiation(self):
        r = _valid_report()
        assert r.fnr_id == "FNR-0001"

    def test_dry_lab_only_true(self):
        r = _valid_report()
        assert r.dry_lab_only is True

    def test_cheap_baselines_list(self):
        r = _valid_report()
        assert len(r.cheap_baselines_checked) == 2

    def test_optional_scores_present(self):
        r = _valid_report()
        assert r.cheap_enemy_score == 0.42
        assert r.family_score == 0.87

    def test_optional_scores_none(self):
        r = _valid_report(cheap_enemy_score=None, family_score=None)
        assert r.cheap_enemy_score is None

    def test_notes_default_empty(self):
        r = _valid_report(notes="")
        assert r.notes == ""


# ── Validation ─────────────────────────────────────────────────────────────────

class TestValidateFamilyNoveltyReport:
    def test_valid_report_passes(self):
        r = _valid_report()
        result = validate_family_novelty_report(r)
        assert result.valid

    def test_invalid_fnr_id_prefix(self):
        r = _valid_report(fnr_id="BAD-0001")
        result = validate_family_novelty_report(r)
        assert not result.valid
        assert any("fnr_id" in v for v in result.violations)

    def test_invalid_cfc_id_prefix(self):
        r = _valid_report(cfc_id="BAD-0001")
        result = validate_family_novelty_report(r)
        assert not result.valid
        assert any("cfc_id" in v for v in result.violations)

    def test_short_family_name_blocked(self):
        r = _valid_report(family_name="AB")
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_empty_cheap_baselines_blocked(self):
        r = _valid_report(cheap_baselines_checked=[])
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_invalid_cheap_baseline_blocked(self):
        r = _valid_report(cheap_baselines_checked=["magic_baseline"])
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_invalid_baseline_outcome_blocked(self):
        r = _valid_report(baseline_comparison_outcome="probably_novel")
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_invalid_novelty_grade_blocked(self):
        r = _valid_report(novelty_strength_grade="excellent")
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_n_known_families_negative_blocked(self):
        r = _valid_report(n_known_families_compared=-1)
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_strong_grade_requires_outside_known_space(self):
        r = _valid_report(novelty_strength_grade="strong", baseline_comparison_outcome="within_known_space")
        result = validate_family_novelty_report(r)
        assert not result.valid
        assert any("strong" in v for v in result.violations)

    def test_not_supported_incompatible_with_outside_known_space(self):
        r = _valid_report(novelty_strength_grade="not_supported", baseline_comparison_outcome="outside_known_space")
        result = validate_family_novelty_report(r)
        assert not result.valid
        assert any("not_supported" in v for v in result.violations)

    def test_strong_grade_blocked_with_comparison_not_run(self):
        r = _valid_report(novelty_strength_grade="strong", baseline_comparison_outcome="comparison_not_run")
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_cheap_enemy_score_above_1_blocked(self):
        r = _valid_report(cheap_enemy_score=1.5)
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_cheap_enemy_score_negative_blocked(self):
        r = _valid_report(cheap_enemy_score=-0.1)
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_family_score_above_1_blocked(self):
        r = _valid_report(family_score=1.1)
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_dry_lab_only_false_blocked(self):
        r = _valid_report(dry_lab_only=False)
        result = validate_family_novelty_report(r)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_empty_limitations_blocked(self):
        r = _valid_report(limitations="")
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_short_limitations_blocked(self):
        r = _valid_report(limitations="Too short")
        result = validate_family_novelty_report(r)
        assert not result.valid

    def test_moderate_grade_with_outside_known_space_valid(self):
        r = _valid_report(novelty_strength_grade="moderate", baseline_comparison_outcome="outside_known_space")
        result = validate_family_novelty_report(r)
        assert result.valid

    def test_weak_grade_with_edge_of_known_space_valid(self):
        r = _valid_report(novelty_strength_grade="weak", baseline_comparison_outcome="edge_of_known_space")
        result = validate_family_novelty_report(r)
        assert result.valid

    def test_not_supported_with_within_known_space_valid(self):
        r = _valid_report(novelty_strength_grade="not_supported", baseline_comparison_outcome="within_known_space")
        result = validate_family_novelty_report(r)
        assert result.valid

    def test_comparison_not_run_with_weak_grade_valid(self):
        r = _valid_report(novelty_strength_grade="weak", baseline_comparison_outcome="comparison_not_run")
        result = validate_family_novelty_report(r)
        assert result.valid

    def test_no_optional_scores_valid(self):
        r = _valid_report(cheap_enemy_score=None, family_score=None)
        result = validate_family_novelty_report(r)
        assert result.valid

    def test_score_boundary_0_valid(self):
        r = _valid_report(cheap_enemy_score=0.0, family_score=0.0)
        result = validate_family_novelty_report(r)
        assert result.valid

    def test_score_boundary_1_valid(self):
        r = _valid_report(cheap_enemy_score=1.0, family_score=1.0)
        result = validate_family_novelty_report(r)
        assert result.valid

    def test_all_five_baselines_valid(self):
        r = _valid_report(cheap_baselines_checked=list(VALID_CHEAP_BASELINES_CHECKED))
        result = validate_family_novelty_report(r)
        assert result.valid

    def test_zero_known_families_compared_valid(self):
        r = _valid_report(n_known_families_compared=0)
        result = validate_family_novelty_report(r)
        assert result.valid


# ── Build ──────────────────────────────────────────────────────────────────────

class TestBuildFamilyNoveltyReport:
    def test_build_valid(self):
        r = build_family_novelty_report(
            fnr_id="FNR-0001",
            cfc_id="CFC-0001",
            family_name="Alpha-Helix Family 1",
            cheap_baselines_checked=["charge_distribution", "length_distribution"],
            baseline_comparison_outcome="outside_known_space",
            novelty_strength_grade="strong",
            n_known_families_compared=5,
            known_families_compared=["defensin_family"],
            limitations="Limited to gram-positive AMP databases only.",
        )
        assert r.fnr_id == "FNR-0001"
        assert r.dry_lab_only is True

    def test_build_enforces_dry_lab_only_true(self):
        r = build_family_novelty_report(
            fnr_id="FNR-0002",
            cfc_id="CFC-0002",
            family_name="Test Family XYZ",
            cheap_baselines_checked=["charge_distribution"],
            baseline_comparison_outcome="outside_known_space",
            novelty_strength_grade="strong",
            n_known_families_compared=3,
            known_families_compared=[],
            limitations="Only charge distribution compared; other baselines pending.",
        )
        assert r.dry_lab_only is True

    def test_build_raises_on_invalid_fnr_id(self):
        with pytest.raises(ValueError):
            build_family_novelty_report(
                fnr_id="BAD-0001",
                cfc_id="CFC-0001",
                family_name="Some Family",
                cheap_baselines_checked=["charge_distribution"],
                baseline_comparison_outcome="outside_known_space",
                novelty_strength_grade="strong",
                n_known_families_compared=1,
                known_families_compared=[],
                limitations="Test limitations string here.",
            )

    def test_build_raises_on_strong_grade_with_within_known(self):
        with pytest.raises(ValueError):
            build_family_novelty_report(
                fnr_id="FNR-0003",
                cfc_id="CFC-0003",
                family_name="Within Known Family",
                cheap_baselines_checked=["charge_distribution"],
                baseline_comparison_outcome="within_known_space",
                novelty_strength_grade="strong",
                n_known_families_compared=5,
                known_families_compared=[],
                limitations="Known space overlap detected; strong grade not justified.",
            )

    def test_build_with_optional_scores(self):
        r = build_family_novelty_report(
            fnr_id="FNR-0004",
            cfc_id="CFC-0004",
            family_name="Scored Family",
            cheap_baselines_checked=["charge_distribution", "hydrophobicity_profile"],
            baseline_comparison_outcome="outside_known_space",
            novelty_strength_grade="strong",
            n_known_families_compared=8,
            known_families_compared=["cathelicidin_family"],
            limitations="Score comparison limited to charge and hydrophobicity only.",
            cheap_enemy_score=0.38,
            family_score=0.91,
        )
        assert r.cheap_enemy_score == 0.38
        assert r.family_score == 0.91

    def test_build_moderate_grade(self):
        r = build_family_novelty_report(
            fnr_id="FNR-0005",
            cfc_id="CFC-0005",
            family_name="Moderate Family",
            cheap_baselines_checked=["charge_distribution"],
            baseline_comparison_outcome="outside_known_space",
            novelty_strength_grade="moderate",
            n_known_families_compared=2,
            known_families_compared=[],
            limitations="Only one hard evidence source; HMM not performed.",
        )
        assert r.novelty_strength_grade == "moderate"


# ── Format ─────────────────────────────────────────────────────────────────────

class TestFormatFamilyNoveltyReport:
    def _build(self, **kwargs):
        defaults = dict(
            fnr_id="FNR-0001",
            cfc_id="CFC-0001",
            family_name="Alpha-Helix Family 1",
            cheap_baselines_checked=["charge_distribution", "length_distribution"],
            baseline_comparison_outcome="outside_known_space",
            novelty_strength_grade="strong",
            n_known_families_compared=5,
            known_families_compared=["defensin_family"],
            limitations="Limited to gram-positive AMP databases only.",
        )
        defaults.update(kwargs)
        return build_family_novelty_report(**defaults)

    def test_format_returns_string(self):
        r = self._build()
        assert isinstance(format_family_novelty_report(r), str)

    def test_format_contains_fnr_id(self):
        r = self._build()
        assert "FNR-0001" in format_family_novelty_report(r)

    def test_format_contains_cfc_id(self):
        r = self._build()
        assert "CFC-0001" in format_family_novelty_report(r)

    def test_format_contains_family_name(self):
        r = self._build()
        assert "Alpha-Helix Family 1" in format_family_novelty_report(r)

    def test_format_contains_novelty_grade(self):
        r = self._build()
        assert "strong" in format_family_novelty_report(r)

    def test_format_contains_baseline_outcome(self):
        r = self._build()
        assert "outside_known_space" in format_family_novelty_report(r)

    def test_format_contains_dry_lab_only_true(self):
        r = self._build()
        assert "dry_lab_only: True" in format_family_novelty_report(r)

    def test_format_contains_baselines(self):
        r = self._build()
        assert "charge_distribution" in format_family_novelty_report(r)

    def test_format_contains_limitations(self):
        r = self._build()
        assert "gram-positive" in format_family_novelty_report(r)

    def test_format_contains_scores_when_present(self):
        r = self._build(cheap_enemy_score=0.42, family_score=0.87)
        out = format_family_novelty_report(r)
        assert "0.420" in out
        assert "0.870" in out

    def test_format_omits_scores_when_none(self):
        r = self._build(cheap_enemy_score=None, family_score=None)
        out = format_family_novelty_report(r)
        assert "Cheap Enemy Score" not in out

    def test_format_multiline(self):
        r = self._build()
        lines = format_family_novelty_report(r).split("\n")
        assert len(lines) >= 7
