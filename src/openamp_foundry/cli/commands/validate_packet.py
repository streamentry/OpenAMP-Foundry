"""CLI validate-packet command: validates an external review packet JSON file."""

from __future__ import annotations

import json
from pathlib import Path


def _parse_candidate_entries(raw: list) -> list:
    """Parse raw candidate entry dicts into CandidateEntry objects."""
    from openamp_foundry.evidence.external_review_packet import CandidateEntry
    entries = []
    for item in raw:
        entries.append(CandidateEntry(
            candidate_id=item.get("candidate_id", ""),
            sequence=item.get("sequence", ""),
            ensemble_score=float(item.get("ensemble_score", 0.0)),
            proof_ladder_level=int(item.get("proof_ladder_level", 0)),
            family=item.get("family", ""),
            selection_rationale=item.get("selection_rationale", ""),
            safety_notes=item.get("safety_notes", ""),
        ))
    return entries


def _parse_benchmark_summaries(raw: list) -> list:
    """Parse raw benchmark summary dicts into BenchmarkSummary objects."""
    from openamp_foundry.evidence.external_review_packet import BenchmarkSummary
    summaries = []
    for item in raw:
        summaries.append(BenchmarkSummary(
            auroc=float(item.get("auroc", 0.0)),
            benchmark_name=item.get("benchmark_name", ""),
            n_positives=int(item.get("n_positives", 0)),
            n_negatives=int(item.get("n_negatives", 0)),
        ))
    return summaries


def _parse_calibration_summary(raw: dict):
    """Parse raw calibration summary dict into CalibrationSummary object."""
    from openamp_foundry.evidence.external_review_packet import CalibrationSummary
    return CalibrationSummary(
        calibration_error=float(raw.get("calibration_error", 0.0)),
        n_bins=int(raw.get("n_bins", 10)),
        assessment=raw.get("assessment", "uninformative"),
    )


def _parse_safety_attestations(raw: dict):
    """Parse raw safety attestations dict into SafetyAttestations object."""
    from openamp_foundry.evidence.external_review_packet import SafetyAttestations
    return SafetyAttestations(
        no_known_toxicity_claim=bool(raw.get("no_known_toxicity_claim", False)),
        dual_use_screened=bool(raw.get("dual_use_screened", False)),
        hemolysis_risk_flagged=bool(raw.get("hemolysis_risk_flagged", False)),
    )


def load_packet_from_json(path: Path):
    """Load an ExternalReviewPacket from a JSON file on disk.

    Raises FileNotFoundError if missing, ValueError if invalid JSON or schema.
    """
    from openamp_foundry.evidence.external_review_packet import ExternalReviewPacket

    if not path.exists():
        raise FileNotFoundError(f"Packet file not found: {path}")

    try:
        with path.open() as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Packet JSON must be an object, got {type(data).__name__}")

    candidate_entries = _parse_candidate_entries(
        data.get("candidate_entries", [])
    )
    benchmark_summaries = _parse_benchmark_summaries(
        data.get("benchmark_summaries", [])
    )

    cal_raw = data.get("calibration_summary", {})
    calibration_summary = _parse_calibration_summary(cal_raw)

    safety_raw = data.get("safety_attestations", {})
    safety_attestations = _parse_safety_attestations(safety_raw)

    return ExternalReviewPacket(
        packet_id=data.get("packet_id", ""),
        candidate_entries=candidate_entries,
        benchmark_summaries=benchmark_summaries,
        calibration_summary=calibration_summary,
        safety_attestations=safety_attestations,
        limitations=data.get("limitations", []),
        pipeline_version=data.get("pipeline_version", ""),
        git_sha=data.get("git_sha", ""),
        dry_lab_only_attestation=bool(data.get("dry_lab_only_attestation", False)),
        calibration_assessment=data.get("calibration_assessment", "uninformative"),
    )


def validate_packet_file(path: Path) -> dict:
    """Validate a packet file and return a result dict.

    Returns dict with keys: path, valid, violations, packet_id, error
    """
    from openamp_foundry.evidence.external_review_packet import (
        validate_external_review_packet,
    )

    try:
        packet = load_packet_from_json(path)
    except (FileNotFoundError, ValueError) as exc:
        return {
            "path": str(path),
            "valid": False,
            "violations": [str(exc)],
            "packet_id": None,
            "error": str(exc),
        }

    result = validate_external_review_packet(packet)
    return {
        "path": str(path),
        "valid": result.valid,
        "violations": list(result.violations),
        "packet_id": result.packet_id,
        "error": None,
    }


def _run_validate_packet(args) -> int:
    """CLI entry point for openamp-foundry validate-packet."""
    path = Path(args.packet_path)
    result = validate_packet_file(path)

    print(f"Packet: {result['path']}")
    if result["packet_id"]:
        print(f"ID:     {result['packet_id']}")

    if result["error"]:
        print(f"ERROR:  {result['error']}")
        return 1

    if result["valid"]:
        print("Status: PASS — packet is valid for external review")
        return 0

    print(f"Status: FAIL — {len(result['violations'])} violation(s)")
    for v in result["violations"]:
        print(f"  VIOLATION: {v}")
    return 1
