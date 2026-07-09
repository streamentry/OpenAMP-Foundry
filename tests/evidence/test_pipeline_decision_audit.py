"""Tests for pipeline decision audit entry schema (Phase M M1)."""

from openamp_foundry.evidence.pipeline_decision_audit import (
    MAX_DESCRIPTION_LENGTH,
    MAX_RATIONALE_LENGTH,
    VALID_DECISION_TYPES,
    VALID_EVIDENCE_LEVELS,
    PipelineDecisionAuditEntry,
    validate_pipeline_decision_audit,
    validate_pipeline_decision_audit_dict,
)


def _valid_entry(**kwargs) -> PipelineDecisionAuditEntry:
    defaults = dict(
        audit_id="AUD-001",
        batch_id="BATCH-001",
        pipeline_version="0.8.9",
        decision_date="2026-07-09",
        decision_type="filter_applied",
        decision_description="Applied hemolysis fraction filter at threshold 0.15.",
        rationale="Threshold pre-specified in BENCHMARK_GOVERNANCE.md based on Wave 0 data.",
        alternatives_considered=["threshold 0.10", "threshold 0.20"],
        affected_candidate_count=47,
        evidence_level=4,
        pre_specified=True,
        reviewer="alice",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return PipelineDecisionAuditEntry(**defaults)


# ── Constants ────────────────────────────────────────────────────────────────


def test_valid_decision_types_count():
    assert len(VALID_DECISION_TYPES) == 7


def test_filter_applied_in_decision_types():
    assert "filter_applied" in VALID_DECISION_TYPES


def test_safety_flag_applied_in_decision_types():
    assert "safety_flag_applied" in VALID_DECISION_TYPES


def test_max_description_length():
    assert MAX_DESCRIPTION_LENGTH == 500


def test_max_rationale_length():
    assert MAX_RATIONALE_LENGTH == 1000


# ── Valid entry ───────────────────────────────────────────────────────────────


def test_valid_entry_passes():
    result = validate_pipeline_decision_audit(_valid_entry())
    assert result.passed
    assert result.errors == []


def test_result_dry_lab_only_true():
    result = validate_pipeline_decision_audit(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_match():
    result = validate_pipeline_decision_audit(_valid_entry())
    assert result.audit_id == "AUD-001"
    assert result.batch_id == "BATCH-001"
    assert result.decision_type == "filter_applied"


def test_valid_all_decision_types():
    for dt in VALID_DECISION_TYPES:
        result = validate_pipeline_decision_audit(_valid_entry(decision_type=dt))
        assert result.passed, f"decision_type '{dt}' should be valid"


def test_valid_all_evidence_levels():
    for level in VALID_EVIDENCE_LEVELS - {1, 2}:
        result = validate_pipeline_decision_audit(_valid_entry(evidence_level=level))
        assert result.passed


def test_valid_empty_alternatives():
    result = validate_pipeline_decision_audit(_valid_entry(alternatives_considered=[]))
    assert result.passed


def test_valid_zero_affected_candidates():
    result = validate_pipeline_decision_audit(_valid_entry(affected_candidate_count=0))
    assert result.passed


# ── audit_id validation ───────────────────────────────────────────────────────


def test_audit_id_missing_prefix_fails():
    result = validate_pipeline_decision_audit(_valid_entry(audit_id="001"))
    assert not result.passed
    assert any("AUD-" in e for e in result.errors)


def test_audit_id_wrong_prefix_fails():
    result = validate_pipeline_decision_audit(_valid_entry(audit_id="DSR-001"))
    assert not result.passed


def test_audit_id_correct_prefix_passes():
    result = validate_pipeline_decision_audit(_valid_entry(audit_id="AUD-XYZ-99"))
    assert result.passed


# ── date validation ───────────────────────────────────────────────────────────


def test_invalid_date_fails():
    result = validate_pipeline_decision_audit(_valid_entry(decision_date="2026/07/09"))
    assert not result.passed
    assert any("YYYY-MM-DD" in e for e in result.errors)


# ── decision_type validation ──────────────────────────────────────────────────


def test_invalid_decision_type_fails():
    result = validate_pipeline_decision_audit(_valid_entry(decision_type="unknown_action"))
    assert not result.passed
    assert any("decision_type" in e for e in result.errors)


# ── description validation ────────────────────────────────────────────────────


def test_empty_description_fails():
    result = validate_pipeline_decision_audit(_valid_entry(decision_description=""))
    assert not result.passed


def test_description_too_long_fails():
    result = validate_pipeline_decision_audit(
        _valid_entry(decision_description="X" * 501)
    )
    assert not result.passed
    assert any("500" in e for e in result.errors)


def test_description_exactly_500_passes():
    result = validate_pipeline_decision_audit(
        _valid_entry(decision_description="X" * 500)
    )
    assert result.passed


# ── rationale validation ──────────────────────────────────────────────────────


def test_empty_rationale_fails():
    result = validate_pipeline_decision_audit(_valid_entry(rationale=""))
    assert not result.passed


def test_rationale_too_long_fails():
    result = validate_pipeline_decision_audit(_valid_entry(rationale="X" * 1001))
    assert not result.passed
    assert any("1000" in e for e in result.errors)


# ── affected_candidate_count validation ───────────────────────────────────────


def test_negative_candidate_count_fails():
    result = validate_pipeline_decision_audit(_valid_entry(affected_candidate_count=-1))
    assert not result.passed


# ── dry_lab_only constraint ───────────────────────────────────────────────────


def test_dry_lab_only_false_fails():
    result = validate_pipeline_decision_audit(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# ── warnings ─────────────────────────────────────────────────────────────────


def test_post_hoc_decision_warns():
    result = validate_pipeline_decision_audit(_valid_entry(pre_specified=False))
    assert result.passed
    assert any("post-hoc" in w or "pre_specified" in w for w in result.warnings)


def test_empty_alternatives_warns():
    result = validate_pipeline_decision_audit(_valid_entry(alternatives_considered=[]))
    assert result.passed
    assert any("alternatives" in w for w in result.warnings)


def test_low_evidence_level_warns():
    result = validate_pipeline_decision_audit(_valid_entry(evidence_level=2))
    assert result.passed
    assert any("low" in w or "limited" in w for w in result.warnings)


def test_zero_affected_candidates_warns():
    result = validate_pipeline_decision_audit(_valid_entry(affected_candidate_count=0))
    assert result.passed
    assert any("0" in w or "no candidates" in w.lower() for w in result.warnings)


def test_full_pre_specified_entry_no_warnings():
    result = validate_pipeline_decision_audit(_valid_entry())
    assert result.passed
    assert result.warnings == []


# ── dict interface ────────────────────────────────────────────────────────────


def test_dict_valid_passes():
    d = dict(
        audit_id="AUD-D01",
        batch_id="BATCH-D01",
        pipeline_version="0.8.9",
        decision_date="2026-07-09",
        decision_type="threshold_chosen",
        decision_description="Set novelty threshold to 0.30.",
        rationale="Based on Wave 0 distribution analysis.",
        alternatives_considered=["0.25", "0.35"],
        affected_candidate_count=12,
        evidence_level=3,
        pre_specified=True,
        reviewer="bob",
        dry_lab_only=True,
    )
    result = validate_pipeline_decision_audit_dict(d)
    assert result.passed


def test_dict_missing_field_fails():
    d = dict(
        audit_id="AUD-D02",
        batch_id="BATCH-D02",
        pipeline_version="0.8.9",
        decision_date="2026-07-09",
        decision_type="filter_applied",
        decision_description="Applied filter.",
        rationale="Pre-specified.",
        alternatives_considered=[],
        affected_candidate_count=5,
        evidence_level=4,
        # missing pre_specified
        reviewer="alice",
    )
    result = validate_pipeline_decision_audit_dict(d)
    assert not result.passed
    assert any("pre_specified" in e for e in result.errors)


def test_dict_dry_lab_only_defaults_true():
    d = dict(
        audit_id="AUD-D03",
        batch_id="BATCH-D03",
        pipeline_version="0.8.9",
        decision_date="2026-07-09",
        decision_type="candidate_rejected",
        decision_description="Rejected due to hemolysis flag.",
        rationale="Safety policy requires rejection.",
        alternatives_considered=["manual review"],
        affected_candidate_count=3,
        evidence_level=4,
        pre_specified=True,
        reviewer="alice",
    )
    result = validate_pipeline_decision_audit_dict(d)
    assert result.passed
    assert result.dry_lab_only is True
