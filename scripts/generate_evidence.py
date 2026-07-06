#!/usr/bin/env python3
"""Compatibility wrapper for the canonical release entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release.generate_evidence import run_ranking_pipeline


if __name__ == "__main__":
    run_ranking_pipeline(
        candidate_path="examples/sequences/demo_candidates.csv",
        reference_path="examples/known_reference/demo_known_amps.csv",
        out_path="outputs/demo_ranked.jsonl",
        report_path="outputs/demo_report.md",
        cert_dir="outputs/evidence",
    )
