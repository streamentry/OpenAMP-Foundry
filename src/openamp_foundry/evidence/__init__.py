"""Evidence certificate layer for OpenAMP Foundry.

Builds machine-readable candidate evidence certificates and validates
them against `schemas/candidate.schema.json`.

Includes synthetic result policy (Phase G G8) which enforces that
synthetic/simulation outputs cannot raise the proof-ladder level
of a candidate — anti-overclaim safeguard.
"""

from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.evidence.schemas import validate_json_schema
from openamp_foundry.evidence.synthetic_result_policy import (
    PROOF_LADDER_LEVELS,
    SyntheticResultPolicyCheck,
    check_synthetic_result_policy,
    run_policy_batch,
    write_policy_check_json,
    write_policy_check_markdown,
)

__all__ = [
    "build_certificate",
    "validate_json_schema",
    "PROOF_LADDER_LEVELS",
    "SyntheticResultPolicyCheck",
    "check_synthetic_result_policy",
    "run_policy_batch",
    "write_policy_check_json",
    "write_policy_check_markdown",
]
