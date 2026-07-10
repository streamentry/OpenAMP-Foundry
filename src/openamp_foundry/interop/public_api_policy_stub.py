"""PAS- public API policy stub schema.

Machine-readable declaration of the safety and privacy properties that any
future public-facing API endpoint for OpenAMP outputs must satisfy.

This stub documents what the API WILL do (or refuse to do) before any
implementation begins — making security and privacy requirements testable
from day one.  When the actual API is built, these stubs become acceptance
criteria.

Key invariants:
  - The public API must never accept raw sequence data (sequence privacy).
  - Rate limiting is declared before any endpoint goes live.
  - Explicit data-not-collected list prevents silent collection.
  - dry_lab_only outputs only: the API cannot return wet-lab results.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_AUTH_METHODS: frozenset[str] = frozenset({
    "api_key",
    "oauth2",
    "none",
})

VALID_DATA_COLLECTION_CATEGORIES: frozenset[str] = frozenset({
    "request_timestamp",
    "endpoint_called",
    "error_code",
    "response_time_ms",
    "api_key_hash",
    "ip_address_hash",
    "query_parameters",
    "raw_sequence_data",
    "candidate_ids",
    "user_agent",
})

REQUIRED_NOT_COLLECTED: tuple[str, ...] = (
    "raw_sequence_data",
    "candidate_ids",
)

MIN_RATE_LIMIT_RPM: int = 1
MAX_RATE_LIMIT_RPM: int = 1000


@dataclass
class PublicApiPolicyStub:
    pas_id: str
    api_version: str
    pipeline_version: str
    auth_method: str
    rate_limit_requests_per_minute: int
    rate_limit_requests_per_day: int
    sequence_data_accepted: bool
    data_collected: list[str]
    data_not_collected: list[str]
    required_not_collected_declared: bool
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_public_api_policy_stub(pas: PublicApiPolicyStub) -> None:
    if not pas.pas_id.startswith("PAS-"):
        raise ValueError(f"pas_id must start with 'PAS-': {pas.pas_id!r}")
    if not pas.api_version:
        raise ValueError("api_version must be non-empty")
    if not pas.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if pas.auth_method not in VALID_AUTH_METHODS:
        raise ValueError(
            f"auth_method {pas.auth_method!r} not in VALID_AUTH_METHODS"
        )
    if pas.rate_limit_requests_per_minute < MIN_RATE_LIMIT_RPM:
        raise ValueError(
            f"rate_limit_requests_per_minute must be >= {MIN_RATE_LIMIT_RPM}"
        )
    if pas.rate_limit_requests_per_minute > MAX_RATE_LIMIT_RPM:
        raise ValueError(
            f"rate_limit_requests_per_minute must be <= {MAX_RATE_LIMIT_RPM}"
        )
    if pas.rate_limit_requests_per_day < pas.rate_limit_requests_per_minute:
        raise ValueError(
            "rate_limit_requests_per_day must be >= rate_limit_requests_per_minute"
        )
    for cat in pas.data_collected:
        if cat not in VALID_DATA_COLLECTION_CATEGORIES:
            raise ValueError(
                f"data_collected category {cat!r} not in VALID_DATA_COLLECTION_CATEGORIES"
            )
    for cat in pas.data_not_collected:
        if cat not in VALID_DATA_COLLECTION_CATEGORIES:
            raise ValueError(
                f"data_not_collected category {cat!r} not in VALID_DATA_COLLECTION_CATEGORIES"
            )
    overlap = set(pas.data_collected) & set(pas.data_not_collected)
    if overlap:
        raise ValueError(
            f"data_collected and data_not_collected overlap: {overlap}"
        )
    if pas.sequence_data_accepted:
        raise ValueError(
            "sequence_data_accepted must be False for public API"
        )
    expected_required_declared = all(
        r in pas.data_not_collected for r in REQUIRED_NOT_COLLECTED
    )
    if pas.required_not_collected_declared != expected_required_declared:
        raise ValueError(
            "required_not_collected_declared inconsistent with data_not_collected"
        )
    if not pas.required_not_collected_declared:
        missing = [r for r in REQUIRED_NOT_COLLECTED if r not in pas.data_not_collected]
        raise ValueError(
            f"data_not_collected must include required items: {missing}"
        )
    if not pas.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not pas.limitations:
        raise ValueError("limitations must be non-empty")
    if not pas.created_at:
        raise ValueError("created_at must be non-empty")


def build_public_api_policy_stub(
    *,
    pas_id: str,
    api_version: str,
    pipeline_version: str,
    auth_method: str,
    rate_limit_requests_per_minute: int,
    rate_limit_requests_per_day: int,
    data_collected: list[str] | None = None,
    data_not_collected: list[str],
    limitations: list[str],
    created_at: str,
) -> PublicApiPolicyStub:
    """Build a PublicApiPolicyStub.

    sequence_data_accepted is always False.
    required_not_collected_declared is auto-computed from data_not_collected.
    """
    data_collected = list(data_collected) if data_collected else []
    data_not_collected = list(data_not_collected)
    not_collected_set = set(data_not_collected)
    required_declared = all(r in not_collected_set for r in REQUIRED_NOT_COLLECTED)
    pas = PublicApiPolicyStub(
        pas_id=pas_id,
        api_version=api_version,
        pipeline_version=pipeline_version,
        auth_method=auth_method,
        rate_limit_requests_per_minute=rate_limit_requests_per_minute,
        rate_limit_requests_per_day=rate_limit_requests_per_day,
        sequence_data_accepted=False,
        data_collected=data_collected,
        data_not_collected=data_not_collected,
        required_not_collected_declared=required_declared,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_public_api_policy_stub(pas)
    return pas


def format_public_api_policy_stub(pas: PublicApiPolicyStub) -> str:
    lines = [
        f"Public API Policy Stub — {pas.pas_id}",
        f"API: {pas.api_version}  |  Pipeline: {pas.pipeline_version}",
        f"Auth: {pas.auth_method}",
        f"Rate limit: {pas.rate_limit_requests_per_minute} rpm / "
        f"{pas.rate_limit_requests_per_day} rpd",
        f"Sequence data accepted: {pas.sequence_data_accepted}",
        f"Required non-collection declared: {pas.required_not_collected_declared}",
    ]
    if pas.data_collected:
        lines.append(f"Data collected: {', '.join(pas.data_collected)}")
    lines.append(f"Data NOT collected: {', '.join(pas.data_not_collected)}")
    lines.append(f"Limitations: {'; '.join(pas.limitations)}")
    lines.append(f"Created: {pas.created_at}")
    lines.append(f"dry_lab_only: {pas.dry_lab_only}")
    return "\n".join(lines)
