#!/usr/bin/env python3
"""Compatibility wrapper for the canonical benchmark entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.benchmarks.benchmark_simulation_ablation import main


if __name__ == "__main__":
    sys.exit(main())
