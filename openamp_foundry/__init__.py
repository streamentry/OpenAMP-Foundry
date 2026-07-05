"""Source-tree import shim for subprocess tests run without installation.

The real package lives under ``src/openamp_foundry``. Pytest adds ``src`` via
configuration, but child Python processes do not inherit pytest's import hook.
This namespace shim makes ``python -m openamp_foundry.cli`` work from repo root.
"""

from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "openamp_foundry"
if _SRC_PACKAGE.exists():
    __path__.append(str(_SRC_PACKAGE))

__version__ = "0.1.0"
