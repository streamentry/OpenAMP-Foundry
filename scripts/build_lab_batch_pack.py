#!/usr/bin/env python3
"""Compatibility wrapper for the canonical lab entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lab.build_lab_batch_pack import main


if __name__ == "__main__":
    sys.exit(main())
