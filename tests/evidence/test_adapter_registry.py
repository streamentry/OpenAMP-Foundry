"""Tests for ARG- adapter registry schema."""

import pytest
from openamp_foundry.evidence.adapter_registry import (
    AdapterRegistry,
    AdapterRegistryEntry,
    VALID_ARG_ADAPTER_STATUSES,
    VALID_ARG_ADAPTER_TYPES,
    VALID_ARG_EVIDENCE_LEVELS,
    RANKING_PERMITTED_STATUSES,
    RANKING_PERMITTED_EVIDENCE_LEVELS,
    build_adapter_registry,
    format_adapter_registry,
    validate_adapter_registry,
)

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

_ACTIVE_VERIFIED = [
    {
        "adapter_id": "ESMFold-v1",
        "adapter_type": "structure_predictor",
        "status": "active",
        "evidence_level": "baseline_verified",
        "version": "1.0.0",
        "scope": "Protein structure prediction from sequence",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["3d_structure_coordinates"],
        "limitations": ["Low accuracy for disordered regions"],
        "baseline_ref": "CBR-001",
        "registered_at": "2026-01-15",
    },
]

_ACTIVE_NONE = [
    {
        "adapter_id": "AMP-BERT-2.0",
        "adapter_type": "sequence_scorer",
        "status": "active",
        "evidence_level": "none",
        "version": "2.0.0",
        "scope": "AMP probability scoring",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["amp_probability"],
        "limitations": ["Trained on known AMPs only"],
        "baseline_ref": "",
        "registered_at": "2026-03-01",
    },
]

_MIXED = [
    {
        "adapter_id": "ESMFold-v1",
        "adapter_type": "structure_predictor",
        "status": "active",
        "evidence_level": "baseline_verified",
        "version": "1.0.0",
        "scope": "Protein structure prediction",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["3d_structure_coordinates"],
        "limitations": ["Low accuracy for disordered regions"],
        "baseline_ref": "CBR-001",
        "registered_at": "2026-01-15",
    },
    {
        "adapter_id": "ToxScan-1.0",
        "adapter_type": "toxicity_filter",
        "status": "experimental",
        "evidence_level": "none",
        "version": "1.0.0",
        "scope": "Hemolysis toxicity screening",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["toxicity_score"],
        "limitations": ["Not validated for clinical use"],
        "baseline_ref": "",
        "registered_at": "2026-02-10",
    },
    {
        "adapter_id": "DockRunner",
        "adapter_type": "simulation_runner",
        "status": "blocked",
        "evidence_level": "none",
        "version": "0.5.0",
        "scope": "Molecular docking simulation",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["docking_score"],
        "limitations": ["Outdated force field parameters"],
        "baseline_ref": "",
        "registered_at": "2026-01-20",
    },
    {
        "adapter_id": "NoveltyNet",
        "adapter_type": "novelty_ranker",
        "status": "active",
        "evidence_level": "wet_lab_validated",
        "version": "3.1.0",
        "scope": "Novelty scoring against known AMP databases",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["novelty_score"],
        "limitations": ["Only compares against APD3 and DRAMP"],
        "baseline_ref": "SEG-002",
        "registered_at": "2026-04-01",
    },
    {
        "adapter_id": "OldScorer",
        "adapter_type": "sequence_scorer",
        "status": "deprecated",
        "evidence_level": "baseline_claimed",
        "version": "0.9.0",
        "scope": "Legacy AMP scoring",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["amp_score"],
        "limitations": ["Replaced by AMP-BERT-2.0"],
        "baseline_ref": "",
        "registered_at": "2025-06-01",
    },
    {
        "adapter_id": "Embedder-X",
        "adapter_type": "embedding_provider",
        "status": "pending_review",
        "evidence_level": "none",
        "version": "0.1.0",
        "scope": "Sequence embedding generation",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["embedding_vector"],
        "limitations": ["Untested on non-AMP sequences"],
        "baseline_ref": "",
        "registered_at": "2026-05-10",
    },
]


def _build(**kwargs):
    defaults = dict(
        arg_id="ARG-001",
        pipeline_version="v3.0",
        entries=_ACTIVE_VERIFIED,
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_adapter_registry(**defaults)


# ---------------------------------------------------------------------------
# Section 1: Constants
# ---------------------------------------------------------------------------


def test_valid_arg_adapter_statuses_is_frozenset():
    assert isinstance(VALID_ARG_ADAPTER_STATUSES, frozenset)


def test_valid_arg_adapter_statuses_contains_active():
    assert "active" in VALID_ARG_ADAPTER_STATUSES


def test_valid_arg_adapter_statuses_contains_deprecated():
    assert "deprecated" in VALID_ARG_ADAPTER_STATUSES


def test_valid_arg_adapter_statuses_contains_experimental():
    assert "experimental" in VALID_ARG_ADAPTER_STATUSES


def test_valid_arg_adapter_statuses_contains_blocked():
    assert "blocked" in VALID_ARG_ADAPTER_STATUSES


def test_valid_arg_adapter_statuses_contains_pending_review():
    assert "pending_review" in VALID_ARG_ADAPTER_STATUSES


def test_valid_arg_adapter_statuses_size():
    assert len(VALID_ARG_ADAPTER_STATUSES) == 5


def test_valid_arg_adapter_types_is_frozenset():
    assert isinstance(VALID_ARG_ADAPTER_TYPES, frozenset)


def test_valid_arg_adapter_types_contains_sequence_scorer():
    assert "sequence_scorer" in VALID_ARG_ADAPTER_TYPES


def test_valid_arg_adapter_types_size():
    assert len(VALID_ARG_ADAPTER_TYPES) == 6


def test_valid_arg_evidence_levels_is_frozenset():
    assert isinstance(VALID_ARG_EVIDENCE_LEVELS, frozenset)


def test_valid_arg_evidence_levels_contains_baseline_verified():
    assert "baseline_verified" in VALID_ARG_EVIDENCE_LEVELS


def test_ranking_permitted_statuses():
    assert RANKING_PERMITTED_STATUSES == frozenset({"active"})


def test_ranking_permitted_evidence_levels():
    assert RANKING_PERMITTED_EVIDENCE_LEVELS == frozenset({
        "baseline_verified", "wet_lab_validated",
    })


# ---------------------------------------------------------------------------
# Section 2: build — happy paths
# ---------------------------------------------------------------------------


def test_build_returns_adapter_registry():
    assert isinstance(_build(), AdapterRegistry)


def test_build_arg_id_stored():
    assert _build().arg_id == "ARG-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v3.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_n_entries_auto_computed():
    assert _build().n_entries == 1


def test_build_n_active_auto_computed():
    assert _build().n_active == 1


def test_build_n_ranking_permitted_auto_computed():
    assert _build().n_ranking_permitted == 1


def test_build_n_blocked_auto_computed():
    r = _build(entries=_MIXED)
    assert r.n_blocked == 1


def test_build_has_unreviewed_active_true():
    r = _build(entries=_ACTIVE_NONE)
    assert r.has_unreviewed_active is True


def test_build_has_unreviewed_active_false():
    assert _build().has_unreviewed_active is False


def test_build_can_affect_ranking_true_active_verified():
    entry = _build().entries[0]
    assert entry.can_affect_ranking is True


def test_build_can_affect_ranking_false_experimental():
    entry_dict = {
        "adapter_id": "TestAdapter",
        "adapter_type": "sequence_scorer",
        "status": "experimental",
        "evidence_level": "none",
        "version": "1.0",
        "scope": "Test scoring",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["amp_probability"],
        "limitations": ["Test limitation"],
        "baseline_ref": "",
        "registered_at": "2026-07-10",
    }
    r = _build(entries=[entry_dict])
    assert r.entries[0].can_affect_ranking is False


def test_build_can_affect_ranking_false_active_none_evidence():
    entry_dict = {
        "adapter_id": "TestAdapter",
        "adapter_type": "sequence_scorer",
        "status": "active",
        "evidence_level": "none",
        "version": "1.0",
        "scope": "Test scoring",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["amp_probability"],
        "limitations": ["Test limitation"],
        "baseline_ref": "",
        "registered_at": "2026-07-10",
    }
    r = _build(entries=[entry_dict])
    assert r.entries[0].can_affect_ranking is False


def test_build_can_affect_ranking_false_blocked():
    entry_dict = {
        "adapter_id": "TestAdapter",
        "adapter_type": "sequence_scorer",
        "status": "blocked",
        "evidence_level": "none",
        "version": "1.0",
        "scope": "Test scoring",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["amp_probability"],
        "limitations": ["Test limitation"],
        "baseline_ref": "",
        "registered_at": "2026-07-10",
    }
    r = _build(entries=[entry_dict])
    assert r.entries[0].can_affect_ranking is False


def test_build_empty_registry():
    r = _build(entries=[])
    assert r.n_entries == 0
    assert r.n_active == 0
    assert r.n_ranking_permitted == 0
    assert r.n_blocked == 0
    assert r.has_unreviewed_active is False


def test_build_all_blocked():
    entries = [
        {
            "adapter_id": "A",
            "adapter_type": "sequence_scorer",
            "status": "blocked",
            "evidence_level": "none",
            "version": "1.0",
            "scope": "Test",
            "inputs": ["amino_acid_sequence"],
            "outputs": ["amp_probability"],
            "limitations": ["Test"],
            "baseline_ref": "",
            "registered_at": "2026-07-10",
        },
        {
            "adapter_id": "B",
            "adapter_type": "toxicity_filter",
            "status": "blocked",
            "evidence_level": "none",
            "version": "1.0",
            "scope": "Test",
            "inputs": ["amino_acid_sequence"],
            "outputs": ["toxicity_score"],
            "limitations": ["Test"],
            "baseline_ref": "",
            "registered_at": "2026-07-10",
        },
    ]
    r = _build(entries=entries)
    assert r.n_entries == 2
    assert r.n_active == 0
    assert r.n_ranking_permitted == 0
    assert r.n_blocked == 2


def test_build_accepts_entry_objects():
    entry = AdapterRegistryEntry(
        adapter_id="ObjAdapter",
        adapter_type="novelty_ranker",
        status="active",
        evidence_level="wet_lab_validated",
        version="2.0",
        scope="Novelty scoring",
        inputs=["amino_acid_sequence"],
        outputs=["novelty_score"],
        limitations=["Limited database"],
        baseline_ref="SEG-005",
        can_affect_ranking=True,
        registered_at="2026-07-10",
    )
    r = _build(entries=[entry])
    assert r.n_entries == 1
    assert r.entries[0].adapter_id == "ObjAdapter"


def test_build_mixed_statuses():
    r = _build(entries=_MIXED)
    assert r.n_entries == 6
    assert r.n_active == 2  # ESMFold-v1, NoveltyNet
    assert r.n_ranking_permitted == 2  # ESMFold-v1, NoveltyNet
    assert r.n_blocked == 1  # DockRunner
    assert r.has_unreviewed_active is False  # both active have verified evidence


# ---------------------------------------------------------------------------
# Section 3: validate — rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_arg_id_prefix():
    with pytest.raises(ValueError, match="ARG-"):
        _build(arg_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_adapter_id():
    entries = [
        {
            "adapter_id": "",
            "adapter_type": "sequence_scorer",
            "status": "active",
            "evidence_level": "baseline_verified",
            "version": "1.0",
            "scope": "Test",
            "inputs": ["amino_acid_sequence"],
            "outputs": ["amp_probability"],
            "limitations": ["Test"],
            "baseline_ref": "CBR-001",
            "registered_at": "2026-07-10",
        },
    ]
    with pytest.raises(ValueError, match="adapter_id"):
        _build(entries=entries)


def test_validate_rejects_invalid_adapter_type():
    entries = [
        {
            "adapter_id": "Test",
            "adapter_type": "invalid_type",
            "status": "active",
            "evidence_level": "none",
            "version": "1.0",
            "scope": "Test",
            "inputs": ["amino_acid_sequence"],
            "outputs": ["amp_probability"],
            "limitations": ["Test"],
            "baseline_ref": "",
            "registered_at": "2026-07-10",
        },
    ]
    with pytest.raises(ValueError, match="VALID_ARG_ADAPTER_TYPES"):
        _build(entries=entries)


def test_validate_rejects_invalid_status():
    entries = [
        {
            "adapter_id": "Test",
            "adapter_type": "sequence_scorer",
            "status": "invalid_status",
            "evidence_level": "none",
            "version": "1.0",
            "scope": "Test",
            "inputs": ["amino_acid_sequence"],
            "outputs": ["amp_probability"],
            "limitations": ["Test"],
            "baseline_ref": "",
            "registered_at": "2026-07-10",
        },
    ]
    with pytest.raises(ValueError, match="VALID_ARG_ADAPTER_STATUSES"):
        _build(entries=entries)


def test_validate_rejects_invalid_evidence_level():
    entries = [
        {
            "adapter_id": "Test",
            "adapter_type": "sequence_scorer",
            "status": "active",
            "evidence_level": "invalid_level",
            "version": "1.0",
            "scope": "Test",
            "inputs": ["amino_acid_sequence"],
            "outputs": ["amp_probability"],
            "limitations": ["Test"],
            "baseline_ref": "",
            "registered_at": "2026-07-10",
        },
    ]
    with pytest.raises(ValueError, match="VALID_ARG_EVIDENCE_LEVELS"):
        _build(entries=entries)


def test_validate_rejects_empty_version():
    entries = [
        {
            "adapter_id": "Test",
            "adapter_type": "sequence_scorer",
            "status": "active",
            "evidence_level": "none",
            "version": "",
            "scope": "Test",
            "inputs": ["amino_acid_sequence"],
            "outputs": ["amp_probability"],
            "limitations": ["Test"],
            "baseline_ref": "",
            "registered_at": "2026-07-10",
        },
    ]
    with pytest.raises(ValueError, match="version"):
        _build(entries=entries)


def test_validate_rejects_empty_inputs():
    entries = [
        {
            "adapter_id": "Test",
            "adapter_type": "sequence_scorer",
            "status": "active",
            "evidence_level": "none",
            "version": "1.0",
            "scope": "Test",
            "inputs": [],
            "outputs": ["amp_probability"],
            "limitations": ["Test"],
            "baseline_ref": "",
            "registered_at": "2026-07-10",
        },
    ]
    with pytest.raises(ValueError, match="inputs"):
        _build(entries=entries)


def test_validate_rejects_empty_outputs():
    entries = [
        {
            "adapter_id": "Test",
            "adapter_type": "sequence_scorer",
            "status": "active",
            "evidence_level": "none",
            "version": "1.0",
            "scope": "Test",
            "inputs": ["amino_acid_sequence"],
            "outputs": [],
            "limitations": ["Test"],
            "baseline_ref": "",
            "registered_at": "2026-07-10",
        },
    ]
    with pytest.raises(ValueError, match="outputs"):
        _build(entries=entries)


def test_validate_rejects_empty_limitations():
    entries = [
        {
            "adapter_id": "Test",
            "adapter_type": "sequence_scorer",
            "status": "active",
            "evidence_level": "none",
            "version": "1.0",
            "scope": "Test",
            "inputs": ["amino_acid_sequence"],
            "outputs": ["amp_probability"],
            "limitations": [],
            "baseline_ref": "",
            "registered_at": "2026-07-10",
        },
    ]
    with pytest.raises(ValueError, match="limitations"):
        _build(entries=entries)


def test_validate_rejects_baseline_ref_missing_when_verified():
    entries = [
        {
            "adapter_id": "Test",
            "adapter_type": "sequence_scorer",
            "status": "active",
            "evidence_level": "baseline_verified",
            "version": "1.0",
            "scope": "Test",
            "inputs": ["amino_acid_sequence"],
            "outputs": ["amp_probability"],
            "limitations": ["Test"],
            "baseline_ref": "",
            "registered_at": "2026-07-10",
        },
    ]
    with pytest.raises(ValueError, match="baseline_ref"):
        _build(entries=entries)


def test_validate_rejects_can_affect_ranking_mismatch_true():
    r = _build()
    r.entries[0].can_affect_ranking = False
    with pytest.raises(ValueError, match="can_affect_ranking"):
        validate_adapter_registry(r)


def test_validate_rejects_can_affect_ranking_mismatch_false():
    entry_dict = {
        "adapter_id": "Test",
        "adapter_type": "sequence_scorer",
        "status": "active",
        "evidence_level": "none",
        "version": "1.0",
        "scope": "Test",
        "inputs": ["amino_acid_sequence"],
        "outputs": ["amp_probability"],
        "limitations": ["Test"],
        "baseline_ref": "",
        "registered_at": "2026-07-10",
    }
    r = _build(entries=[entry_dict])
    r.entries[0].can_affect_ranking = True
    with pytest.raises(ValueError, match="can_affect_ranking"):
        validate_adapter_registry(r)


def test_validate_rejects_dry_lab_only_false():
    r = _build()
    r.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_adapter_registry(r)


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_n_entries_mismatch():
    r = _build()
    r.n_entries = 999
    with pytest.raises(ValueError, match="n_entries"):
        validate_adapter_registry(r)


def test_validate_rejects_n_active_mismatch():
    r = _build(entries=_MIXED)
    r.n_active = 999
    with pytest.raises(ValueError, match="n_active"):
        validate_adapter_registry(r)


def test_validate_rejects_has_unreviewed_active_mismatch():
    r = _build()
    r.has_unreviewed_active = True
    with pytest.raises(ValueError, match="has_unreviewed_active"):
        validate_adapter_registry(r)


# ---------------------------------------------------------------------------
# Section 4: format
# ---------------------------------------------------------------------------


def test_format_contains_arg_id():
    assert "ARG-001" in format_adapter_registry(_build())


def test_format_contains_pipeline_version():
    assert "v3.0" in format_adapter_registry(_build())


def test_format_contains_entry_count():
    text = format_adapter_registry(_build())
    assert "1 total" in text


def test_format_contains_active_count():
    text = format_adapter_registry(_build())
    assert "1 active" in text


def test_format_contains_ranking_permitted_count():
    text = format_adapter_registry(_build())
    assert "1 ranking-permitted" in text


def test_format_contains_blocked_count():
    r = _build(entries=_MIXED)
    text = format_adapter_registry(r)
    assert "1 blocked" in text


def test_format_contains_unreviewed_warning():
    r = _build(entries=_ACTIVE_NONE)
    text = format_adapter_registry(r)
    assert "WARNING" in text


def test_format_is_string():
    assert isinstance(format_adapter_registry(_build()), str)
