"""Benchmark deprecation banner system — Phase C C8.

Prevents stale benchmark authority by providing:
1. Detection of deprecated benchmark cards in the registry
2. Human-readable deprecation banners for each deprecated card
3. A strict governance check that fails if deprecated benchmarks are used
   in official ranking decisions without explicit override

Usage:
    from openamp_foundry.evidence.benchmark_deprecation import (
        check_no_deprecated_in_ranking,
        get_deprecated_cards,
        build_deprecation_banner,
        print_all_deprecation_banners,
    )

    # In CI or ranking pipeline:
    check_no_deprecated_in_ranking(registry)  # raises if any card is deprecated

    # For user-facing warnings:
    print_all_deprecation_banners(registry)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openamp_foundry.evidence.benchmark_card import BenchmarkCard

_BANNER_WIDTH = 72
_BANNER_CHAR = "!"


class DeprecatedBenchmarkError(Exception):
    """Raised when a deprecated benchmark is used in a ranking context."""


def get_deprecated_cards(
    registry: list["BenchmarkCard"],
) -> list["BenchmarkCard"]:
    """Return all deprecated BenchmarkCards from the given registry."""
    return [card for card in registry if card.deprecated]


def get_active_cards(
    registry: list["BenchmarkCard"],
) -> list["BenchmarkCard"]:
    """Return all non-deprecated BenchmarkCards from the given registry."""
    return [card for card in registry if not card.deprecated]


def build_deprecation_banner(card: "BenchmarkCard") -> str:
    """Build a human-readable deprecation banner for a deprecated benchmark.

    The banner is designed to be impossible to miss: it uses a visible
    header, states the benchmark ID and name, and quotes the notes field
    which must explain the deprecation reason.
    """
    sep = _BANNER_CHAR * _BANNER_WIDTH
    lines = [
        sep,
        f"DEPRECATED BENCHMARK — {card.bmc_id}",
        sep,
        f"Name:    {card.benchmark_name}",
        f"Target:  {card.measurement_target}",
        f"Reason:  {card.notes or '(no reason given)'}",
        sep,
        "WARNING: This benchmark is DEPRECATED and must NOT be used to make",
        "ranking decisions or support candidate selection claims.",
        "Remove or replace it before publishing results.",
        sep,
    ]
    return "\n".join(lines)


def print_all_deprecation_banners(
    registry: list["BenchmarkCard"],
) -> list[str]:
    """Print deprecation banners for all deprecated cards.

    Returns the list of banners printed (useful for testing without capturing stdout).
    """
    deprecated = get_deprecated_cards(registry)
    banners: list[str] = []
    for card in deprecated:
        banner = build_deprecation_banner(card)
        print(banner)
        banners.append(banner)
    return banners


def check_no_deprecated_in_ranking(
    registry: list["BenchmarkCard"],
    allow_deprecated: bool = False,
) -> None:
    """Strict governance check: raise if any deprecated benchmark is in the registry.

    Args:
        registry: List of BenchmarkCard instances to check.
        allow_deprecated: If True, skip the check (for testing only — must be
                          documented in code review).

    Raises:
        DeprecatedBenchmarkError: If any card in the registry is deprecated.
    """
    if allow_deprecated:
        return

    deprecated = get_deprecated_cards(registry)
    if deprecated:
        names = ", ".join(f"{c.bmc_id} ({c.benchmark_name!r})" for c in deprecated)
        raise DeprecatedBenchmarkError(
            f"Deprecated benchmarks found in ranking registry: {names}. "
            "Remove deprecated cards from the registry before running official "
            "ranking. Set allow_deprecated=True only in test contexts with "
            "explicit code-review approval."
        )


def deprecation_status_report(
    registry: list["BenchmarkCard"],
) -> dict:
    """Return a machine-readable deprecation status report for the registry.

    Returns a dict with:
        total: int — total cards in registry
        active: int — non-deprecated cards
        deprecated: int — deprecated cards
        deprecated_ids: list[str] — BMC IDs of deprecated cards
        all_active: bool — True if no deprecated cards
    """
    deprecated = get_deprecated_cards(registry)
    return {
        "total": len(registry),
        "active": len(registry) - len(deprecated),
        "deprecated": len(deprecated),
        "deprecated_ids": [c.bmc_id for c in deprecated],
        "all_active": len(deprecated) == 0,
    }
