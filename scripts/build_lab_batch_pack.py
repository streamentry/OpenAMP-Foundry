"""Build a zip archive with everything a lab partner needs.

Collects candidate CSV, evidence certificates, protocol references,
controls manifest, and data return templates into a single zip.
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


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_panel_rows(panel_csv: Path) -> list[dict[str, str]]:
    with panel_csv.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _candidate_identity_rows(panel_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    identities: list[dict[str, Any]] = []
    for row in panel_rows:
        candidate_id = row.get("candidate_id", "").strip()
        sequence = row.get("sequence", "").strip().upper()
        if not candidate_id or not sequence:
            continue
        identities.append({
            "candidate_id": candidate_id,
            "sequence_sha256": _sha256_text(sequence),
            "sequence_length": len(sequence),
        })
    return identities


def _synthesis_order_digest(panel_rows: list[dict[str, str]]) -> str:
    """Hash the ordered candidate identity list, not vendor instructions."""
    lines = []
    for row in panel_rows:
        candidate_id = row.get("candidate_id", "").strip()
        sequence = row.get("sequence", "").strip().upper()
        if candidate_id and sequence:
            lines.append(f"{candidate_id},{sequence}")
    return _sha256_text("\n".join(lines) + "\n")


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

        panel_hash_ok = _sha256_bytes(panel_bytes) == custody.get("panel_csv_sha256")

        panel_text = panel_bytes.decode("utf-8")
        panel_rows = list(csv.DictReader(panel_text.splitlines()))
        expected_identities = _candidate_identity_rows(panel_rows)
        identities_ok = expected_identities == custody.get("candidate_identities", [])
        order_ok = _synthesis_order_digest(panel_rows) == custody.get("synthesis_order_sha256")

        evidence_ok = True
        evidence_hashes = custody.get("evidence_certificate_sha256", {})
        for archive_name, expected_hash in evidence_hashes.items():
            if archive_name not in names or _sha256_bytes(zf.read(archive_name)) != expected_hash:
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
    """Build a lab batch pack zip.

    Returns manifest dict with included files and counts.
    """
    panel_p = Path(panel_csv)
    evidence_p = Path(evidence_dir)
    out_p = Path(out_zip)
    schema_p = Path(data_return_schema)

    if not panel_p.exists():
        return {"error": f"Panel CSV not found: {panel_csv}"}
    if not evidence_p.exists():
        return {"error": f"Evidence directory not found: {evidence_dir}"}

    panel_rows = _read_panel_rows(panel_p)
    candidate_identities = _candidate_identity_rows(panel_rows)
    panel_data = panel_p.read_bytes()
    panel_csv_sha256 = _sha256_bytes(panel_data)
    synthesis_order_sha256 = _synthesis_order_digest(panel_rows)

    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
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
    }

    with zipfile.ZipFile(out_p, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Panel CSV
        zf.writestr("panel.csv", panel_data)
        manifest["panel_csv_size"] = len(panel_data)

        # 2. Evidence certificates
        ev_count = 0
        evidence_hashes: dict[str, str] = {}
        for f in sorted(evidence_p.iterdir()):
            if f.suffix == ".json":
                archive_name = f"evidence/{f.name}"
                evidence_bytes = f.read_bytes()
                zf.writestr(archive_name, evidence_bytes)
                evidence_hashes[archive_name] = _sha256_bytes(evidence_bytes)
                ev_count += 1
                manifest["included_candidates"].append(f.stem)
        manifest["evidence_count"] = ev_count
        manifest["evidence_certificate_sha256"] = evidence_hashes

        # 3. Protocol references (as a README)
        protocols = protocol_docs or [
            "docs/LAB_PARTNER_ONBOARDING.md",
            "docs/ASSAY_PREREGISTRATION.md",
            "docs/WET_LAB_HANDOFF.md",
        ]
        protocol_lines = [
            "# Lab Batch Pack — Protocol References",
            "",
            "See the following documents for assay protocols and instructions:",
            "",
        ]
        for doc_path in protocols:
            doc_p = Path(doc_path)
            if doc_p.exists():
                zf.write(str(doc_p), f"protocols/{doc_p.name}")
                protocol_lines.append(f"- {doc_path}")
                manifest["included_protocols"].append(doc_path)
        zf.writestr("protocols/README.md", "\n".join(protocol_lines))

        # 4. Controls manifest
        ctrl = controls or [
            {"candidate_id": "SEED-001_VAR_064",
             "role": "POSITIVE_CONTROL",
             "sequence": "GIGKFLHSAKKFGKAFVGEIMNS",
             "expected_mic_range_ugml": "4-32",
             "notes": "Magainin-1 derivative; validates MIC assay"},
        ]
        zf.writestr("controls_manifest.json", json.dumps(ctrl, indent=2))
        manifest["controls"] = ctrl

        # 5. Data return template (empty JSON per schema)
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

        # 6. Chain-of-custody identity hashes
        custody = {
            "chain_of_custody_version": "1.0",
            "scope": (
                "Dry-lab identity check only. Hashes verify that candidate IDs, "
                "sequences, panel ordering, and evidence certificate files did not drift."
            ),
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

        # 6. Batch README
        readme = [
            "# OpenAMP Foundry — Lab Batch Pack",
            "",
            f"Generated: {manifest['generated_at']}",
            f"Candidates: {ev_count}",
            f"Protocols: {len(manifest['included_protocols'])}",
            "",
            "## Contents",
            "",
            "- panel.csv — Candidate list with IDs and sequences",
            "- evidence/ — Evidence certificates (one JSON per candidate)",
            "- protocols/ — Assay protocol documents",
            "- controls_manifest.json — Positive/negative control sequences",
            "- data_return_template.json — Empty JSON template per lab_result.schema.json",
            "- chain_of_custody.json — SHA-256 identity hashes for panel, sequences, and evidence files",
            "- MANIFEST.json — Machine-readable archive manifest",
            "",
            "## Identity Verification",
            "",
            "Before using returned results, verify that panel and evidence files match:",
            "",
            "    python scripts/build_lab_batch_pack.py --verify-pack <pack.zip>",
            "",
            "These hashes verify identity only. They are not evidence of activity, safety, synthesis success, or clinical utility.",
            "",
            "## Return Data",
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
    parser.add_argument("--verify-pack", default=None, help="Verify an existing lab batch pack zip")
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
