"""Build a fail-closed zip archive with everything a lab partner needs.

Collects the candidate panel, matching evidence certificates, safe review
references, controls manifest, data-return template, and chain-of-custody
hashes into a single archive.

This module intentionally validates identity and review completeness. It does
not provide wet-lab procedures and does not assert biological activity.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_PANEL_COLUMNS = {"candidate_id", "sequence"}
DEFAULT_PROTOCOL_DOCS = [
    "docs/review/LAB_PARTNER_ONBOARDING.md",
    "docs/review/PRE_REGISTERED_PILOT_TEMPLATE.md",
    "docs/review/EXTERNAL_REVIEW_PACKET.md",
    "docs/evidence/PROOF_LADDER.md",
    "docs/trust/TRUST_CENTER.md",
]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _candidate_identity_rows(
    panel_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    identities: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in panel_rows:
        candidate_id = row.get("candidate_id", "").strip()
        sequence = row.get("sequence", "").strip().upper()
        if not candidate_id or not sequence:
            continue
        if candidate_id in seen:
            raise ValueError(f"Duplicate candidate_id in panel CSV: {candidate_id}")
        seen.add(candidate_id)
        identities.append(
            {
                "candidate_id": candidate_id,
                "sequence_sha256": _sha256_text(sequence),
                "sequence_length": len(sequence),
            }
        )
    return identities


def _read_panel_rows(panel_csv: Path) -> list[dict[str, str]]:
    with panel_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_PANEL_COLUMNS - fieldnames)
        if missing:
            raise ValueError(
                "Panel CSV is missing required column(s): " + ", ".join(missing)
            )
        rows = list(reader)

    if not rows:
        raise ValueError("Panel CSV contains no candidate rows.")

    if not _candidate_identity_rows(rows):
        raise ValueError("Panel CSV contains no valid candidate identities.")

    return rows


def _synthesis_order_digest(panel_rows: list[dict[str, str]]) -> str:
    """Hash the ordered candidate identity list, not vendor instructions."""
    lines = []
    for row in panel_rows:
        candidate_id = row.get("candidate_id", "").strip()
        sequence = row.get("sequence", "").strip().upper()
        if candidate_id and sequence:
            lines.append(f"{candidate_id},{sequence}")
    return _sha256_text("\n".join(lines) + "\n")


def _protocol_doc_paths(
    protocol_docs: list[str] | None,
) -> tuple[list[Path], list[str]]:
    docs = DEFAULT_PROTOCOL_DOCS if protocol_docs is None else protocol_docs
    if not docs:
        return [], ["at least one safe review reference document is required"]

    paths = [Path(doc) for doc in docs]
    missing = [str(path) for path in paths if not path.exists()]
    return paths, missing


def verify_batch_pack(zip_path: str | Path) -> dict[str, Any]:
    """Verify chain-of-custody hashes inside a lab batch pack zip."""
    zip_p = Path(zip_path)
    if not zip_p.exists():
        return {"status": "error", "error": f"Pack not found: {zip_path}"}

    with zipfile.ZipFile(zip_p) as zf:
        names = set(zf.namelist())
        required = {"panel.csv", "chain_of_custody.json", "MANIFEST.json"}
        missing = sorted(required - names)
        if missing:
            return {"status": "failed", "missing_files": missing}

        panel_bytes = zf.read("panel.csv")
        custody = json.loads(zf.read("chain_of_custody.json").decode("utf-8"))
        manifest = json.loads(zf.read("MANIFEST.json").decode("utf-8"))

        panel_hash_ok = _sha256_bytes(panel_bytes) == custody.get(
            "panel_csv_sha256"
        )

        panel_text = panel_bytes.decode("utf-8")
        panel_rows = list(csv.DictReader(panel_text.splitlines()))
        expected_identities = _candidate_identity_rows(panel_rows)
        identities_ok = expected_identities == custody.get("candidate_identities", [])
        order_ok = _synthesis_order_digest(panel_rows) == custody.get(
            "synthesis_order_sha256"
        )

        evidence_ok = True
        evidence_hashes = custody.get("evidence_certificate_sha256", {})
        for archive_name, expected_hash in evidence_hashes.items():
            if archive_name not in names:
                evidence_ok = False
                break
            evidence_hash = _sha256_bytes(zf.read(archive_name))
            if evidence_hash != expected_hash:
                evidence_ok = False
                break

    ok = panel_hash_ok and identities_ok and order_ok and evidence_ok
    return {
        "status": "ok" if ok else "failed",
        "pack": str(zip_p),
        "panel_hash_ok": panel_hash_ok,
        "candidate_identity_hashes_ok": identities_ok,
        "synthesis_order_hash_ok": order_ok,
        "evidence_hashes_ok": evidence_ok,
        "candidate_count": len(expected_identities),
        "manifest_candidate_count": manifest.get("candidate_count"),
    }


def build_batch_pack(
    panel_csv: str,
    evidence_dir: str,
    out_zip: str,
    protocol_docs: list[str] | None = None,
    controls: list[dict[str, Any]] | None = None,
    data_return_schema: str = "schemas/lab_result.schema.json",
) -> dict[str, Any]:
    """Build a fail-closed lab batch pack zip.

    Returns a manifest dict with included files and counts, or an ``error`` dict.
    """
    panel_p = Path(panel_csv)
    evidence_p = Path(evidence_dir)
    out_p = Path(out_zip)
    schema_p = Path(data_return_schema)

    if not panel_p.exists():
        return {"error": f"Panel CSV not found: {panel_csv}"}
    if not evidence_p.exists():
        return {"error": f"Evidence directory not found: {evidence_dir}"}

    try:
        panel_rows = _read_panel_rows(panel_p)
    except ValueError as exc:
        return {"error": str(exc)}

    protocol_paths, missing_protocol_docs = _protocol_doc_paths(protocol_docs)
    if missing_protocol_docs:
        return {
            "error": "Missing protocol/reference document(s): "
            + ", ".join(missing_protocol_docs),
            "missing_protocol_docs": missing_protocol_docs,
        }

    candidate_identities = _candidate_identity_rows(panel_rows)
    panel_ids = {row["candidate_id"] for row in candidate_identities}

    evidence_files = {
        f.stem: f
        for f in sorted(evidence_p.iterdir())
        if f.is_file() and f.suffix == ".json"
    }
    evidence_ids = set(evidence_files)

    missing_evidence = sorted(panel_ids - evidence_ids)
    extra_evidence = sorted(evidence_ids - panel_ids)
    if missing_evidence:
        return {
            "error": "Missing evidence certificate(s) for panel candidate(s): "
            + ", ".join(missing_evidence),
            "missing_evidence": missing_evidence,
        }
    if extra_evidence:
        error = "Evidence directory contains certificate(s) not present in panel CSV: "
        return {
            "error": error + ", ".join(extra_evidence),
            "extra_evidence": extra_evidence,
        }

    panel_data = panel_p.read_bytes()
    panel_csv_sha256 = _sha256_bytes(panel_data)
    synthesis_order_sha256 = _synthesis_order_digest(panel_rows)

    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack_standard": "fail_closed_lab_handoff_v1",
        "panel_csv": panel_csv,
        "panel_csv_sha256": panel_csv_sha256,
        "synthesis_order_sha256": synthesis_order_sha256,
        "candidate_count": len(candidate_identities),
        "evidence_count": 0,
        "included_protocols": [],
        "included_candidates": [],
        "candidate_identities": candidate_identities,
        "data_return_template": None,
        "controls": controls or [],
        "strict_identity_checks": {
            "panel_schema_required": sorted(REQUIRED_PANEL_COLUMNS),
            "evidence_must_match_panel_exactly": True,
            "protocol_references_required": True,
        },
    }

    out_p.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_p, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("panel.csv", panel_data)
        manifest["panel_csv_size"] = len(panel_data)

        evidence_hashes: dict[str, str] = {}
        for candidate_id in sorted(panel_ids):
            f = evidence_files[candidate_id]
            archive_name = f"evidence/{f.name}"
            evidence_bytes = f.read_bytes()
            zf.writestr(archive_name, evidence_bytes)
            evidence_hashes[archive_name] = _sha256_bytes(evidence_bytes)
            manifest["included_candidates"].append(candidate_id)
        manifest["evidence_count"] = len(evidence_hashes)
        manifest["evidence_certificate_sha256"] = evidence_hashes

        protocol_lines = [
            "# Lab Batch Pack — Safe Review References",
            "",
            "The archive includes these review documents, not experimental instructions:",
            "",
        ]
        for doc_p in protocol_paths:
            zf.write(str(doc_p), f"protocols/{doc_p.name}")
            protocol_lines.append(f"- {doc_p}")
            manifest["included_protocols"].append(str(doc_p))
        zf.writestr("protocols/README.md", "\n".join(protocol_lines) + "\n")

        ctrl = controls or [
            {
                "candidate_id": "SEED-001_VAR_064",
                "role": "POSITIVE_CONTROL",
                "sequence": "GIGKFLHSAKKFGKAFVGEIMNS",
                "expected_mic_range_ugml": "4-32",
                "notes": "Magainin-1 derivative; validates MIC assay",
            },
        ]
        zf.writestr("controls_manifest.json", json.dumps(ctrl, indent=2))
        manifest["controls"] = ctrl

        if schema_p.exists():
            template: dict[str, Any] = {
                "result_id": "REPLACE_WITH_UUID",
                "candidate_id": "REPLACE_WITH_CANDIDATE_ID",
                "assay_type": "MIC",
                "organism_or_cell_line": "Escherichia coli ATCC 25922",
                "result_value": 0.0,
                "result_unit": "ug/mL",
                "positive_control_passed": True,
                "negative_control_passed": True,
                "assay_date": "YYYY-MM-DD",
                "replicate_count": 3,
                "performed_by_lab": "LAB_NAME",
                "computational_candidate_certificate_hash": "REPLACE",
                "disclaimer": "SYNTHETIC — replace with real data",
            }
            zf.writestr("data_return_template.json", json.dumps(template, indent=2))
            manifest["data_return_template"] = str(schema_p)

        custody = {
            "chain_of_custody_version": "1.1",
            "scope": (
                "Dry-lab identity check only. Hashes verify that candidate IDs, "
                "sequences, panel ordering, and evidence certificate files did not drift."
            ),
            "pack_standard": "fail_closed_lab_handoff_v1",
            "strict_identity_checks": manifest["strict_identity_checks"],
            "not_evidence_of": [
                "biological activity",
                "mammalian safety",
                "synthesis success",
                "clinical utility",
            ],
            "panel_csv_sha256": panel_csv_sha256,
            "synthesis_order_sha256": synthesis_order_sha256,
            "candidate_identities": candidate_identities,
            "evidence_certificate_sha256": evidence_hashes,
        }
        zf.writestr("chain_of_custody.json", json.dumps(custody, indent=2))
        zf.writestr("MANIFEST.json", json.dumps(manifest, indent=2))

        readme = [
            "# OpenAMP Foundry — Lab Batch Pack",
            "",
            f"Generated: {manifest['generated_at']}",
            f"Candidates: {manifest['candidate_count']}",
            f"Evidence certificates: {manifest['evidence_count']}",
            f"Review references: {len(manifest['included_protocols'])}",
            "",
            "## Contents",
            "",
            "- panel.csv — Candidate list with IDs and sequences",
            "- evidence/ — Evidence certificates, one JSON per panel candidate",
            "- protocols/ — Safe review references, not wet-lab procedures",
            "- controls_manifest.json — Positive/negative control metadata",
            "- data_return_template.json — Empty JSON template per lab_result.schema.json",
            "- chain_of_custody.json — SHA-256 identity hashes",
            "- MANIFEST.json — Machine-readable archive manifest",
            "",
            "## Fail-Closed Checks Applied",
            "",
            "- panel.csv must contain candidate_id and sequence columns",
            "- every panel candidate must have exactly one evidence certificate",
            "- evidence_dir must not contain certificates outside the panel",
            "- safe review-reference documents must be bundled",
            "",
            "## Identity Verification",
            "",
            "Before using returned results, verify that panel and evidence files match:",
            "",
            "    python scripts/lab/build_lab_batch_pack.py --verify-pack <pack.zip>",
            "",
            "These hashes verify identity only. They are not evidence of activity, safety, "
            "synthesis success, or clinical utility.",
            "",
            "After assaying, return one JSON file per candidate per assay type.",
            "Use the data_return_template.json as a starting point.",
            "Place all files in a single directory and run:",
            "",
            "    python scripts/check_wave1_pass_fail.py --results-dir <dir>",
            "",
        ]
        zf.writestr("README.md", "\n".join(readme))

    manifest["out_zip"] = str(out_p)
    manifest["zip_size_bytes"] = out_p.stat().st_size
    return manifest


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build lab batch pack zip")
    parser.add_argument("--panel-csv", default="outputs/wave1_final_panel.csv")
    parser.add_argument("--evidence-dir", default="outputs/evidence_wave0_5")
    parser.add_argument("--out", default="outputs/lab_batch_pack.zip")
    parser.add_argument("--manifest-out", default=None, help="JSON manifest path")
    parser.add_argument(
        "--verify-pack",
        default=None,
        help="Verify an existing lab batch pack zip",
    )
    args = parser.parse_args()

    if args.verify_pack:
        result = verify_batch_pack(args.verify_pack)
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "ok" else 3

    manifest = build_batch_pack(
        panel_csv=args.panel_csv,
        evidence_dir=args.evidence_dir,
        out_zip=args.out,
    )
    if "error" in manifest:
        print(f"Error: {manifest['error']}", file=sys.stderr)
        return 2

    print(json.dumps(manifest, indent=2))
    if args.manifest_out:
        Path(args.manifest_out).write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
