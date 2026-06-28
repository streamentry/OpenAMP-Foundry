from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path("configs/pipeline.yaml")


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)
    if result is None:
        raise ValueError(f"Config file is empty: {path}")
    return result
