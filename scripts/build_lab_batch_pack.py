"""Build a zip archive with everything a lab partner needs.

Collects candidate CSV, evidence certificates, protocol references,
controls manifest, and data return templates into a single zip.
"""

from __future__ import annotations

import csv
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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

    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "panel_csv": panel_csv,
        "evidence_count": 0,
        "included_protocols": [],
        "included_candidates": [],
        "data_return_template": None,
        "controls": controls or [],
    }

    with zipfile.ZipFile(out_p, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Panel CSV
        panel_data = panel_p.read_bytes()
        zf.writestr("panel.csv", panel_data)
        manifest["panel_csv_size"] = len(panel_data)

        # 2. Evidence certificates
        ev_count = 0
        for f in sorted(evidence_p.iterdir()):
            if f.suffix == ".json":
                zf.write(str(f), f"evidence/{f.name}")
                ev_count += 1
                manifest["included_candidates"].append(f.stem)
        manifest["evidence_count"] = ev_count

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
            schema = json.loads(schema_p.read_text())
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
    args = parser.parse_args()

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
