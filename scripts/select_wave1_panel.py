#!/usr/bin/env python3
"""Compatibility wrapper for the canonical wave entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.waves.select_wave1_panel import main


if __name__ == "__main__":
    sys.exit(main())
