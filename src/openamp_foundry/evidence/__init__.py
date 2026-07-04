"""Evidence certificate layer for OpenAMP Foundry.

Builds machine-readable candidate evidence certificates and validates
them against `schemas/candidate.schema.json`.
"""

from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.evidence.schemas import validate_json_schema

__all__ = [
    "build_certificate",
    "validate_json_schema",
]
