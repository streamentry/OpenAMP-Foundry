import pytest
from openamp_foundry.evidence.audit_chain_completeness import (
    AuditChainEntry,
    AuditChainResult,
    validate_audit_chain,
    validate_audit_chain_dict,
    CHAIN_LINK_FIELDS,
    CHAIN_LINK_COUNT,
    AUDITOR_EMAIL_HINT,
    IMPLAUSIBLE_YEAR_THRESHOLD,
)


def _valid_entry(**overrides) -> AuditChainEntry:
    base = dict(
        chain_id="ACH-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.3",
        audit_date="2026-07-10",
        has_sequence_input=True,
        has_benchmark_results=True,
        has_filter_log=True,
        has_score_decomposition=True,
        has_selection_rationale=True,
        has_evidence_certificate=True,
        has_claim_mappings=True,
        has_pipeline_decision_audit=True,
        has_reviewer_briefing=True,
        missing_links=[],
        auditor="auditor@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return AuditChainEntry(**base)


def _valid_dict(**overrides) -> dict:
    base = dict(
        chain_id="ACH-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.3",
        audit_date="2026-07-10",
        has_sequence_input=True,
        has_benchmark_results=True,
        has_filter_log=True,
        has_score_decomposition=True,
        has_selection_rationale=True,
        has_evidence_certificate=True,
        has_claim_mappings=True,
        has_pipeline_decision_audit=True,
        has_reviewer_briefing=True,
        missing_links=[],
        auditor="auditor@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return base


# --- Happy path ---

def test_complete_chain_passes():
    result = validate_audit_chain(_valid_entry())
    assert result.passed
    assert result.errors == []
    assert result.warnings == []


def test_result_dry_lab_only_always_true():
    result = validate_audit_chain(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_populated():
    result = validate_audit_chain(_valid_entry())
    assert result.chain_id == "ACH-001"
    assert result.batch_id == "BATCH-001"
    assert result.missing_link_count == 0


def test_missing_link_count_zero_when_complete():
    result = validate_audit_chain(_valid_entry())
    assert result.missing_link_count == 0


# --- chain_id validation ---

def test_chain_id_must_start_with_ach():
    result = validate_audit_chain(_valid_entry(chain_id="AUDIT-001"))
    assert not result.passed
    assert any("ACH-" in e for e in result.errors)


def test_chain_id_empty_fails():
    result = validate_audit_chain(_valid_entry(chain_id=""))
    assert not result.passed


def test_chain_id_ach_prefix_valid():
    result = validate_audit_chain(_valid_entry(chain_id="ACH-999"))
    assert result.passed


# --- auditor validation ---

def test_empty_auditor_fails():
    result = validate_audit_chain(_valid_entry(auditor=""))
    assert not result.passed
    assert any("auditor" in e for e in result.errors)


def test_auditor_without_email_warns():
    result = validate_audit_chain(_valid_entry(auditor="Dr. Jane Smith"))
    assert result.passed
    assert any("email" in w.lower() or "contact" in w.lower() for w in result.warnings)


def test_auditor_with_email_no_warn():
    result = validate_audit_chain(_valid_entry(auditor="jane@example.com"))
    assert result.passed
    assert not any("email" in w.lower() for w in result.warnings)


# --- dry_lab_only ---

def test_dry_lab_only_false_fails():
    result = validate_audit_chain(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# --- individual chain link failures ---

def test_missing_sequence_input_fails():
    result = validate_audit_chain(
        _valid_entry(has_sequence_input=False, missing_links=["has_sequence_input"])
    )
    assert not result.passed
    assert any("has_sequence_input" in e for e in result.errors)


def test_missing_benchmark_results_fails():
    result = validate_audit_chain(
        _valid_entry(has_benchmark_results=False, missing_links=["has_benchmark_results"])
    )
    assert not result.passed
    assert any("has_benchmark_results" in e for e in result.errors)


def test_missing_filter_log_fails():
    result = validate_audit_chain(
        _valid_entry(has_filter_log=False, missing_links=["has_filter_log"])
    )
    assert not result.passed


def test_missing_score_decomposition_fails():
    result = validate_audit_chain(
        _valid_entry(has_score_decomposition=False, missing_links=["has_score_decomposition"])
    )
    assert not result.passed


def test_missing_selection_rationale_fails():
    result = validate_audit_chain(
        _valid_entry(has_selection_rationale=False, missing_links=["has_selection_rationale"])
    )
    assert not result.passed


def test_missing_evidence_certificate_fails():
    result = validate_audit_chain(
        _valid_entry(has_evidence_certificate=False, missing_links=["has_evidence_certificate"])
    )
    assert not result.passed


def test_missing_claim_mappings_fails():
    result = validate_audit_chain(
        _valid_entry(has_claim_mappings=False, missing_links=["has_claim_mappings"])
    )
    assert not result.passed


def test_missing_pipeline_decision_audit_fails():
    result = validate_audit_chain(
        _valid_entry(has_pipeline_decision_audit=False, missing_links=["has_pipeline_decision_audit"])
    )
    assert not result.passed


def test_missing_reviewer_briefing_fails():
    result = validate_audit_chain(
        _valid_entry(has_reviewer_briefing=False, missing_links=["has_reviewer_briefing"])
    )
    assert not result.passed


def test_multiple_missing_links_all_reported():
    result = validate_audit_chain(
        _valid_entry(
            has_sequence_input=False,
            has_filter_log=False,
            missing_links=["has_sequence_input", "has_filter_log"],
        )
    )
    assert not result.passed
    assert any("has_sequence_input" in e for e in result.errors)
    assert any("has_filter_log" in e for e in result.errors)
    assert result.missing_link_count == 2


# --- missing_links consistency ---

def test_missing_links_mismatch_extra_declared_fails():
    result = validate_audit_chain(
        _valid_entry(missing_links=["has_sequence_input"])
    )
    assert not result.passed
    assert any("declares" in e and "missing" in e for e in result.errors)


def test_missing_links_mismatch_overlooked_fails():
    result = validate_audit_chain(
        _valid_entry(
            has_filter_log=False,
            missing_links=[],
        )
    )
    assert not result.passed
    assert any("omits" in e for e in result.errors)


def test_missing_links_empty_when_complete_passes():
    result = validate_audit_chain(_valid_entry(missing_links=[]))
    assert result.passed


# --- implausible date ---

def test_future_date_warns():
    result = validate_audit_chain(_valid_entry(audit_date="2031-01-01"))
    assert result.passed
    assert any(str(IMPLAUSIBLE_YEAR_THRESHOLD) in w or "2031" in w for w in result.warnings)


def test_current_date_no_date_warning():
    result = validate_audit_chain(_valid_entry(audit_date="2026-07-10"))
    assert not any(str(IMPLAUSIBLE_YEAR_THRESHOLD) in w for w in result.warnings)


def test_invalid_date_format_no_crash():
    result = validate_audit_chain(_valid_entry(audit_date="not-a-date"))
    assert result.passed


# --- dict interface ---

def test_valid_dict_passes():
    result = validate_audit_chain_dict(_valid_dict())
    assert result.passed


def test_missing_chain_id_fails():
    d = _valid_dict()
    del d["chain_id"]
    result = validate_audit_chain_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_missing_has_sequence_input_fails():
    d = _valid_dict()
    del d["has_sequence_input"]
    result = validate_audit_chain_dict(d)
    assert not result.passed


def test_missing_auditor_fails():
    d = _valid_dict()
    del d["auditor"]
    result = validate_audit_chain_dict(d)
    assert not result.passed


def test_dict_dry_lab_only_defaults_true():
    d = _valid_dict()
    del d["dry_lab_only"]
    result = validate_audit_chain_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_multiple_missing_fields():
    d = {}
    result = validate_audit_chain_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_dict_false_link_reports_error():
    d = _valid_dict()
    d["has_reviewer_briefing"] = False
    d["missing_links"] = ["has_reviewer_briefing"]
    result = validate_audit_chain_dict(d)
    assert not result.passed
    assert any("has_reviewer_briefing" in e for e in result.errors)


# --- constants ---

def test_chain_link_fields_count():
    assert len(CHAIN_LINK_FIELDS) == 9


def test_chain_link_count_value():
    assert CHAIN_LINK_COUNT == 9


def test_auditor_email_hint_value():
    assert AUDITOR_EMAIL_HINT == "@"


def test_implausible_year_threshold_value():
    assert IMPLAUSIBLE_YEAR_THRESHOLD == 2030


def test_chain_link_fields_contains_all_expected():
    expected = {
        "has_sequence_input",
        "has_benchmark_results",
        "has_filter_log",
        "has_score_decomposition",
        "has_selection_rationale",
        "has_evidence_certificate",
        "has_claim_mappings",
        "has_pipeline_decision_audit",
        "has_reviewer_briefing",
    }
    assert set(CHAIN_LINK_FIELDS) == expected
