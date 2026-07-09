"""Tests for the simulation-evidence packet assembler (Phase H H10)."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from openamp_foundry.simulation.evidence_packet import (
    SimulationEvidencePacket,
    assemble_evidence_packet,
    evidence_packet_summary,
)
from openamp_foundry.simulation.interfaces import SimulationResult


def _make_result(
    module: str = "membrane_proxy",
    scope: list[str] | None = None,
) -> SimulationResult:
    return SimulationResult(
        module=module,
        version="0.1.0",
        scope=scope or ["bacterial_membrane_binding"],
        scores={"binding_energy": 0.75},
        uncertainty=0.1,
        calibration_set=None,
        validated_against=["APD3"],
        notes=[],
    )


# ── assemble_evidence_packet returns SimulationEvidencePacket ──────

def test_assemble_returns_packet():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
    )
    assert isinstance(packet, SimulationEvidencePacket)


# ── all_checks_passed=True when all sub-checks pass ────────────────

def test_all_checks_passed_all_green():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
    )
    assert packet.all_checks_passed is True
    assert packet.failure_reasons == []


# ── all_checks_passed=False when deprecation blocked ───────────────

def test_deprecation_blocked_fails():
    result = _make_result(module="dummy_membrane_proxy")
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=1,
        baseline_beaten=True,
    )
    assert packet.all_checks_passed is False
    assert any("deprecated" in r.lower() for r in packet.failure_reasons)


# ── all_checks_passed=False when scope uncovered ───────────────────

def test_scope_uncovered_fails():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["fungal_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
    )
    assert packet.all_checks_passed is False
    assert any("scope" in r.lower() for r in packet.failure_reasons)


# ── all_checks_passed=False when baseline capped ───────────────────

def test_baseline_capped_fails():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=False,
    )
    assert packet.all_checks_passed is False
    assert any("baseline" in r.lower() for r in packet.failure_reasons)


# ── all_checks_passed=False when adapter gate fails ────────────────

def test_adapter_timeout_fails():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
        adapter_timeout=True,
    )
    assert packet.all_checks_passed is False
    assert any("timeout" in r.lower() for r in packet.failure_reasons)


# ── failure_reasons non-empty when any check fails ─────────────────

def test_failure_reasons_non_empty_on_failure():
    result = _make_result(module="dummy_membrane_proxy")
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=False,
    )
    assert len(packet.failure_reasons) > 0


# ── failure_reasons empty when all pass ────────────────────────────

def test_failure_reasons_empty_on_pass():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
    )
    assert packet.failure_reasons == []


# ── effective_evidence_level capped when baseline not beaten ───────

def test_effective_level_capped_when_baseline_not_beaten():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=False,
    )
    assert packet.effective_evidence_level < packet.claimed_evidence_level


# ── dry_lab_only always True ───────────────────────────────────────

def test_dry_lab_only_always_true():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
    )
    assert packet.dry_lab_only is True


# ── evidence_packet_summary returns correct keys ───────────────────

def test_summary_has_correct_keys():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
    )
    summary = evidence_packet_summary(packet)
    expected_keys = {
        "module_id", "claimed_evidence_level", "effective_evidence_level",
        "all_checks_passed", "failure_reasons", "dry_lab_only",
    }
    assert set(summary.keys()) == expected_keys


# ── evidence_packet_summary dry_lab_only=True ──────────────────────

def test_summary_dry_lab_only_true():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
    )
    summary = evidence_packet_summary(packet)
    assert summary["dry_lab_only"] is True


# ── deprecated module → all_checks_passed=False ────────────────────

def test_deprecated_module_all_checks_false():
    result = _make_result(module="dummy_membrane_proxy")
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=1,
        baseline_beaten=True,
    )
    assert packet.all_checks_passed is False


# ── adapter timeout → all_checks_passed=False ──────────────────────

def test_adapter_timeout_all_checks_false():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
        adapter_timeout=True,
    )
    assert packet.all_checks_passed is False


# ── membrane_proxy + correct scope + baseline_beaten=True → pass ───

def test_membrane_proxy_bacterial_pass():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
    )
    assert packet.all_checks_passed is True
    assert packet.effective_evidence_level == 2


# ── membrane_proxy + fungal_binding → scope uncovered fail ─────────

def test_membrane_proxy_fungal_scope_fails():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["fungal_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
    )
    assert packet.all_checks_passed is False
    assert any("scope" in r.lower() for r in packet.failure_reasons)


# ── assemble_evidence_packet stores all fields correctly ───────────

def test_packet_stores_all_fields():
    result = _make_result()
    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=["bacterial_membrane_binding"],
        claimed_evidence_level=2,
        baseline_beaten=True,
    )
    assert packet.module_id == "membrane_proxy"
    assert packet.claimed_evidence_level == 2
    assert packet.baseline_beaten is True
    assert isinstance(packet.deprecation_check, dict)
    assert isinstance(packet.scope_check, dict)
    assert isinstance(packet.baseline_check, dict)
    assert isinstance(packet.adapter_gate, dict)
