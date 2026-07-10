"""CLI first-run report: summarises demo outputs for new users."""

from __future__ import annotations

import json
from pathlib import Path


_DEFAULT_OUTPUTS_DIR = Path("outputs")

_CLAIM_BOUNDARY_NOTICE = (
    "NOTE: All outputs are computational (dry-lab only). "
    "Scores are NOT biological activity predictions. "
    "Candidates are nominated for review, not validated."
)


def _count_jsonl_lines(path: Path) -> int:
    """Return number of non-empty lines in a JSONL file, or 0 if missing."""
    if not path.exists():
        return 0
    count = 0
    with path.open() as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _read_manifest(path: Path) -> dict:
    """Return manifest dict, or empty dict if missing/invalid."""
    if not path.exists():
        return {}
    try:
        with path.open() as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _count_certs(cert_dir: Path) -> int:
    """Return number of evidence certificate files in cert_dir."""
    if not cert_dir.is_dir():
        return 0
    return sum(1 for _ in cert_dir.iterdir() if _.is_file())


def _report_exists(report_path: Path) -> bool:
    """Return True if the demo report file exists and is non-empty."""
    return report_path.exists() and report_path.stat().st_size > 0


def build_first_run_report(outputs_dir: Path | None = None) -> dict:
    """Build a structured first-run report dict from demo outputs.

    Returns a dict with keys:
      outputs_dir, demo_run_found, candidate_count, cert_count,
      report_exists, manifest_keys, claim_boundary_notice, sections
    """
    if outputs_dir is None:
        outputs_dir = _DEFAULT_OUTPUTS_DIR

    ranked_path = outputs_dir / "demo_ranked.jsonl"
    report_path = outputs_dir / "demo_report.md"
    cert_dir = outputs_dir / "evidence"
    manifest_path = outputs_dir / "run_manifest.json"

    candidate_count = _count_jsonl_lines(ranked_path)
    cert_count = _count_certs(cert_dir)
    report_exists = _report_exists(report_path)
    manifest = _read_manifest(manifest_path)

    demo_run_found = candidate_count > 0 or cert_count > 0 or report_exists

    sections = []

    if demo_run_found:
        sections.append(
            f"Ranked candidates found: {candidate_count} "
            f"(in {ranked_path})"
        )
        sections.append(
            f"Evidence certificates found: {cert_count} "
            f"(in {cert_dir}/)"
        )
        if report_exists:
            sections.append(f"Demo report: {report_path}")
        else:
            sections.append(f"Demo report not found at {report_path}")
        if manifest:
            sections.append(
                f"Run manifest: {len(manifest)} key(s) recorded "
                f"(in {manifest_path})"
            )
    else:
        sections.append(
            "No demo outputs found. Run `make demo` first, "
            "then re-run this report."
        )

    sections.append(_CLAIM_BOUNDARY_NOTICE)

    return {
        "outputs_dir": str(outputs_dir),
        "demo_run_found": demo_run_found,
        "candidate_count": candidate_count,
        "cert_count": cert_count,
        "report_exists": report_exists,
        "manifest_keys": list(manifest.keys()),
        "claim_boundary_notice": _CLAIM_BOUNDARY_NOTICE,
        "sections": sections,
    }


def format_first_run_report(report: dict) -> str:
    """Format a first-run report dict as a human-readable string."""
    lines = ["=== OpenAMP Foundry — First-Run Report ===", ""]
    for section in report["sections"]:
        lines.append(f"  {section}")
    lines.append("")
    lines.append(
        "What to read next: docs/getting-started/FIRST_RUN_WALKTHROUGH.md"
    )
    return "\n".join(lines)


def _run_first_run_report(args) -> int:
    """CLI entry point for openamp-foundry first-run-report."""
    outputs_dir = getattr(args, "outputs_dir", None)
    if outputs_dir is not None:
        outputs_dir = Path(outputs_dir)
    report = build_first_run_report(outputs_dir=outputs_dir)
    print(format_first_run_report(report))
    return 0
