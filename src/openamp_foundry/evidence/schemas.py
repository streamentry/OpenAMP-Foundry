from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema

from openamp_foundry.utils.io import read_json


def validate_json_schema(payload: dict[str, Any], schema_path: str | Path) -> None:
    schema = read_json(schema_path)
    jsonschema.validate(instance=payload, schema=schema)
