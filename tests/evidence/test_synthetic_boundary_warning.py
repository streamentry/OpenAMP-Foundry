"""Tests for SBW- synthetic boundary warning schema."""

import pytest
from openamp_foundry.evidence.synthetic_boundary_warning import (
    SyntheticBoundaryWarning,
    SyntheticDataRecord,
    VALID_SBW_DATA_TYPES,
    VALID_SBW_VERDICTS,
    SYNTHETIC_LABEL_REQUIRED,
    CANNOT_SUPPORT_BIOLOGICAL_CLAIM,
    WARNING_TEXT,
    build_synthetic_boundary_warning,
    format_synthetic_boundary_warning,
    validate_synthetic_boundary_warning,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LIMITATIONS = ["Dry-lab only, not biological validation."]

ALL_LABELLED_RECORDS = [
    dict(record_id="MIC-001", data_type="mic_simulation",
         source_model="AMPScannerV2", synthetic_label=True,
         warning_attached=True),
    dict(record_id="STR-001", data_type="structure_prediction",
         source_model="ESMFold", synthetic_label=True,
         warning_attached=True),
]

SOME_UNLABELLED_RECORDS = [
    dict(record_id="MIC-001", data_type="mic_simulation",
         source_model="AMPScannerV2", synthetic_label=True,
         warning_attached=True),
    dict(record_id="DOCK-001", data_type="docking_score",
         source_model="AutoDockVina", synthetic_label=False,
         warning_attached=False),
]


def _build(**kwargs):
    defaults = dict(
        sbw_id="SBW-001",
        pipeline_version="v1.0",
        artifact_id="artifact-run-001",
        synthetic_records=[dict(r) for r in ALL_LABELLED_RECORDS],
        limitations=list(LIMITATIONS),
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_synthetic_boundary_warning(**defaults)


def _make_sbw(**kwargs):
    defaults = dict(
        sbw_id="SBW-001",
        pipeline_version="v1.0",
        artifact_id="artifact-run-001",
        synthetic_records=[
            SyntheticDataRecord(
                record_id="MIC-001", data_type="mic_simulation",
                source_model="AMPScannerV2",
                synthetic_label=True, warning_attached=True,
                is_compliant=True,
            ),
            SyntheticDataRecord(
                record_id="STR-001", data_type="structure_prediction",
                source_model="ESMFold",
                synthetic_label=True, warning_attached=True,
                is_compliant=True,
            ),
        ],
        n_records=2, n_labelled=2, n_unlabelled=0,
        unlabelled_ids=[], verdict="labelled",
        limitations=list(LIMITATIONS), created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return SyntheticBoundaryWarning(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants (12 tests)
# ---------------------------------------------------------------------------


def test_valid_sbw_data_types_is_frozenset():
    assert isinstance(VALID_SBW_DATA_TYPES, frozenset)


def test_valid_sbw_data_types_has_eight():
    assert len(VALID_SBW_DATA_TYPES) == 8


def test_valid_sbw_data_types_contains_expected_values():
    expected = {
        "mic_simulation", "structure_prediction", "docking_score",
        "md_trajectory", "hemolysis_simulation", "toxicity_simulation",
        "embedding_vector", "activity_score",
    }
    assert VALID_SBW_DATA_TYPES == expected


def test_valid_sbw_verdicts_is_frozenset():
    assert isinstance(VALID_SBW_VERDICTS, frozenset)


def test_valid_sbw_verdicts_has_three():
    assert len(VALID_SBW_VERDICTS) == 3


def test_valid_sbw_verdicts_contains_labelled():
    assert "labelled" in VALID_SBW_VERDICTS


def test_valid_sbw_verdicts_contains_partially_labelled():
    assert "partially_labelled" in VALID_SBW_VERDICTS


def test_valid_sbw_verdicts_contains_unlabelled():
    assert "unlabelled" in VALID_SBW_VERDICTS


def test_synthetic_label_required_true():
    assert SYNTHETIC_LABEL_REQUIRED is True


def test_cannot_support_biological_claim_true():
    assert CANNOT_SUPPORT_BIOLOGICAL_CLAIM is True


def test_warning_text_is_non_empty_string():
    assert isinstance(WARNING_TEXT, str)
    assert len(WARNING_TEXT) > 0


def test_warning_text_contains_synthetic_data_disclaimer():
    assert "SYNTHETIC DATA" in WARNING_TEXT
    assert "computational simulation" in WARNING_TEXT


# ---------------------------------------------------------------------------
# 2. build – happy paths (18 tests)
# ---------------------------------------------------------------------------


def test_build_returns_synthetic_boundary_warning():
    assert isinstance(_build(), SyntheticBoundaryWarning)


def test_build_labelled_verdict():
    assert _build().verdict == "labelled"


def test_build_partially_labelled_verdict():
    r = _build(synthetic_records=SOME_UNLABELLED_RECORDS)
    assert r.verdict == "partially_labelled"


def test_build_unlabelled_zero_records():
    r = _build(synthetic_records=[])
    assert r.verdict == "unlabelled"


def test_build_unlabelled_none_compliant():
    records = [
        dict(record_id="MIC-001", data_type="mic_simulation",
             source_model="AMPScannerV2",
             synthetic_label=False, warning_attached=False),
    ]
    r = _build(synthetic_records=records)
    assert r.verdict == "unlabelled"


def test_build_n_records_count():
    assert _build().n_records == 2


def test_build_n_labelled_count():
    assert _build().n_labelled == 2
    r = _build(synthetic_records=SOME_UNLABELLED_RECORDS)
    assert r.n_labelled == 1


def test_build_n_unlabelled_count():
    assert _build().n_unlabelled == 0
    r = _build(synthetic_records=SOME_UNLABELLED_RECORDS)
    assert r.n_unlabelled == 1


def test_build_unlabelled_ids_list():
    r = _build(synthetic_records=SOME_UNLABELLED_RECORDS)
    assert r.unlabelled_ids == ["DOCK-001"]


def test_build_is_compliant_true():
    assert _build().synthetic_records[0].is_compliant is True


def test_build_is_compliant_false_when_missing_label_or_warning():
    for synthetic_label, warning_attached in [(True, False), (False, True), (False, False)]:
        records = [
            dict(record_id="MIC-001", data_type="mic_simulation",
                 source_model="AMPScannerV2",
                 synthetic_label=synthetic_label,
                 warning_attached=warning_attached),
        ]
        r = _build(synthetic_records=records)
        assert r.synthetic_records[0].is_compliant is False


def test_build_cannot_support_biological_claim_true():
    assert _build().cannot_support_biological_claim is True


def test_build_sbw_id_stored():
    assert _build(sbw_id="SBW-099").sbw_id == "SBW-099"


def test_build_pipeline_version_stored():
    assert _build(pipeline_version="v2.0").pipeline_version == "v2.0"


def test_build_artifact_id_stored():
    assert _build(artifact_id="run-099").artifact_id == "run-099"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_limitations_stored():
    r = _build(limitations=["lim1", "lim2"])
    assert r.limitations == ["lim1", "lim2"]


def test_build_created_at_stored():
    assert _build(created_at="2026-07-11").created_at == "2026-07-11"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases (18 tests)
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_sbw_id_prefix():
    with pytest.raises(ValueError, match="SBW-"):
        _build(sbw_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_artifact_id():
    with pytest.raises(ValueError):
        _build(artifact_id="")


def test_validate_rejects_empty_record_id():
    sbw = _make_sbw()
    sbw.synthetic_records[0].record_id = ""
    with pytest.raises(ValueError, match="record_id"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_invalid_data_type():
    sbw = _make_sbw()
    sbw.synthetic_records[0].data_type = "invalid_simulation"
    with pytest.raises(ValueError, match="data_type"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_empty_source_model():
    sbw = _make_sbw()
    sbw.synthetic_records[0].source_model = ""
    with pytest.raises(ValueError, match="source_model"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_is_compliant_mismatch():
    sbw = _make_sbw()
    sbw.synthetic_records[0].is_compliant = False
    with pytest.raises(ValueError, match="is_compliant"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_n_records_mismatch():
    sbw = _build()
    sbw.n_records = 99
    with pytest.raises(ValueError, match="n_records"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_n_labelled_mismatch():
    sbw = _build()
    sbw.n_labelled = 99
    with pytest.raises(ValueError, match="n_labelled"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_n_unlabelled_mismatch():
    sbw = _build()
    sbw.n_unlabelled = 99
    with pytest.raises(ValueError, match="n_unlabelled"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_unlabelled_ids_mismatch():
    sbw = _build()
    sbw.unlabelled_ids = ["some/record.yaml"]
    with pytest.raises(ValueError, match="unlabelled_ids"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_verdict_not_in_valid_set():
    sbw = _build()
    sbw.verdict = "invalid_verdict"
    with pytest.raises(ValueError, match="verdict"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_verdict_inconsistent():
    sbw = _build()
    sbw.verdict = "unlabelled"
    with pytest.raises(ValueError, match="verdict"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_cannot_support_biological_claim_false():
    sbw = _build()
    sbw.cannot_support_biological_claim = False
    with pytest.raises(ValueError, match="cannot_support_biological_claim"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_dry_lab_only_false():
    sbw = _build()
    sbw.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_synthetic_boundary_warning(sbw)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_empty_verdict_string():
    sbw = _build()
    sbw.verdict = ""
    with pytest.raises(ValueError, match="verdict"):
        validate_synthetic_boundary_warning(sbw)


# ---------------------------------------------------------------------------
# 4. format (8 tests)
# ---------------------------------------------------------------------------


def test_format_contains_sbw_id():
    assert "SBW-001" in format_synthetic_boundary_warning(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_synthetic_boundary_warning(_build())


def test_format_contains_artifact_id():
    assert "artifact-run-001" in format_synthetic_boundary_warning(_build())


def test_format_contains_verdict():
    assert "labelled" in format_synthetic_boundary_warning(_build())


def test_format_contains_n_records_and_n_labelled():
    output = format_synthetic_boundary_warning(_build())
    assert "2" in output


def test_format_contains_unlabelled_ids_when_present():
    r = _build(synthetic_records=SOME_UNLABELLED_RECORDS)
    output = format_synthetic_boundary_warning(r)
    assert "Unlabelled:" in output
    assert "DOCK-001" in output


def test_format_contains_warning_text():
    output = format_synthetic_boundary_warning(_build())
    assert "SYNTHETIC DATA" in output


def test_format_is_string():
    assert isinstance(format_synthetic_boundary_warning(_build()), str)
