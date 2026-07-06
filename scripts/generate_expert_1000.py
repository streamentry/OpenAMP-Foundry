#!/usr/bin/env python3
"""Compatibility wrapper for the canonical research entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research.generate_expert_1000 import main


if __name__ == "__main__":
    main()
