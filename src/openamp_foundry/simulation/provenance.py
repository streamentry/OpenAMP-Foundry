"""Simulation-result provenance chain — traceable audit trail for every result.

Every simulation result must carry a traceable provenance record (which module
produced it, with what version, run_id, and when) so that results can be
audited, reproduced, or invalidated later without relying on memory.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SimulationProvenanceRecord:
    run_id: str
    module_id: str
    module_version: str
    timestamp_utc: str
    input_hash: str
    result_hash: str
    calibration_set: str | None = None
    notes: list[str] = field(default_factory=list)
    dry_lab_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_provenance_record(
    run_id: str,
    module_id: str,
    module_version: str,
    timestamp_utc: str,
    input_sequence: str,
    result_scores: dict[str, float],
    calibration_set: str | None = None,
    notes: list[str] | None = None,
) -> SimulationProvenanceRecord:
    input_hash = hashlib.sha256(input_sequence.encode()).hexdigest()
    scores_json = json.dumps(result_scores, sort_keys=True).encode()
    result_hash = hashlib.sha256(scores_json).hexdigest()
    return SimulationProvenanceRecord(
        run_id=run_id,
        module_id=module_id,
        module_version=module_version,
        timestamp_utc=timestamp_utc,
        input_hash=input_hash,
        result_hash=result_hash,
        calibration_set=calibration_set,
        notes=notes or [],
    )


def validate_provenance_record(record: SimulationProvenanceRecord) -> list[str]:
    errors: list[str] = []
    if not record.run_id:
        errors.append("run_id must be non-empty")
    if not record.module_id:
        errors.append("module_id must be non-empty")
    if not record.module_version:
        errors.append("module_version must be non-empty")
    if not record.timestamp_utc or "T" not in record.timestamp_utc:
        errors.append("timestamp_utc must be an ISO 8601 string containing 'T'")
    if len(record.input_hash) != 64 or not _is_hex(record.input_hash):
        errors.append("input_hash must be a 64-character hex string")
    if len(record.result_hash) != 64 or not _is_hex(record.result_hash):
        errors.append("result_hash must be a 64-character hex string")
    if record.dry_lab_only is not True:
        errors.append("dry_lab_only must be True")
    return errors


def _is_hex(s: str) -> bool:
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def provenance_summary(records: list[SimulationProvenanceRecord]) -> dict:
    modules = sorted({r.module_id for r in records})
    return {
        "total": len(records),
        "modules": modules,
        "runs": [r.run_id for r in records],
        "dry_lab_only": True,
    }
