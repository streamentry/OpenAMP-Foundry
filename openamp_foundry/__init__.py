"""Source-tree import shim for repo-root execution.

The canonical package lives under ``src/openamp_foundry``. This shim exists only
so repo-root subprocesses such as ``python -m openamp_foundry.cli`` continue to
work without an editable install. It must stay behaviorally thin and should not
become a second source of package logic.
"""

from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

_ROOT = Path(__file__).resolve().parent.parent
_SRC_PACKAGE = _ROOT / "src" / "openamp_foundry"

_raw_path = list(extend_path(__path__, __name__))
if _SRC_PACKAGE.exists():
    _raw_path.append(str(_SRC_PACKAGE))

# Deduplicate while preserving order so import resolution stays predictable.
_deduped_path: list[str] = []
for entry in _raw_path:
    if entry not in _deduped_path:
        _deduped_path.append(entry)
__path__ = _deduped_path

__version__ = "0.1.0"
