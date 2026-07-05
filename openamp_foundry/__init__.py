from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parent.parent
_SRC_PACKAGE = _ROOT / "src" / "openamp_foundry"

__path__ = [str(_SRC_PACKAGE)]
__version__ = "0.1.0"
