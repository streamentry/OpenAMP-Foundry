"""
Changelog entry schema and generator for PR-title-based changelogs.

J1: History without manual maintenance. Parses PR titles in
conventional-commit format into structured changelog entries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

KNOWN_ENTRY_TYPES: frozenset[str] = frozenset({
    "feat",
    "fix",
    "docs",
    "test",
    "refactor",
    "chore",
    "perf",
    "ci",
    "build",
    "style",
})

KNOWN_PHASES: frozenset[str] = frozenset({
    "Phase A",
    "Phase B",
    "Phase C",
    "Phase D",
    "Phase E",
    "Phase F",
    "Phase G",
    "Phase H",
    "Phase I",
    "Phase J",
    "Phase P",
})

UNKNOWN_TYPE: str = "other"
UNKNOWN_SCOPE: str = "unknown"

_CONVENTIONAL_COMMIT_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?:\s+(?P<description>.+)$",
    re.IGNORECASE,
)

_PHASE_RE = re.compile(r"(Phase\s+[A-Z])", re.IGNORECASE)


@dataclass
class ChangelogEntry:
    """Structured representation of a single changelog entry derived from a PR title."""

    pr_number: int
    pr_title: str
    commit_sha: str
    merge_date: str
    entry_type: str
    scope: str
    description: str


@dataclass
class Changelog:
    """Collection of changelog entries for a version or date range."""

    version: str
    generated_at: str
    entries: list[ChangelogEntry]
    entry_count: int


def parse_pr_title(title: str) -> tuple[str, str, str]:
    """
    Parse a PR title in conventional-commit format into (type, scope, description).

    Handles:
    - 'feat: Phase E E1 description' → ('feat', 'Phase E', 'Phase E E1 description')
    - 'fix(Phase B): description' → ('fix', 'Phase B', 'description')
    - 'docs: some docs change' → ('docs', 'unknown', 'some docs change')
    - 'anything else' → ('other', 'unknown', 'anything else')
    """
    if not title or not title.strip():
        return (UNKNOWN_TYPE, UNKNOWN_SCOPE, "")

    title = title.strip()
    match = _CONVENTIONAL_COMMIT_RE.match(title)

    if match:
        raw_type = match.group("type").lower()
        raw_scope = match.group("scope") or ""
        description = match.group("description").strip()
        entry_type = raw_type if raw_type in KNOWN_ENTRY_TYPES else UNKNOWN_TYPE

        if raw_scope:
            scope = raw_scope.strip()
        else:
            phase_match = _PHASE_RE.search(description)
            scope = phase_match.group(1) if phase_match else UNKNOWN_SCOPE

        return (entry_type, scope, description)

    phase_match = _PHASE_RE.search(title)
    scope = phase_match.group(1) if phase_match else UNKNOWN_SCOPE
    return (UNKNOWN_TYPE, scope, title)


def build_changelog_entry(
    pr_number: int,
    pr_title: str,
    commit_sha: str,
    merge_date: str,
) -> ChangelogEntry:
    """
    Build a ChangelogEntry from a PR number, title, commit SHA, and merge date.

    Parses the title with parse_pr_title to extract type, scope, and description.
    """
    entry_type, scope, description = parse_pr_title(pr_title)
    return ChangelogEntry(
        pr_number=pr_number,
        pr_title=pr_title,
        commit_sha=commit_sha,
        merge_date=merge_date,
        entry_type=entry_type,
        scope=scope,
        description=description,
    )


def group_entries_by_type(
    entries: list[ChangelogEntry],
) -> dict[str, list[ChangelogEntry]]:
    """
    Group changelog entries by their entry_type.

    Returns a dict mapping type → list of entries.
    Types are sorted alphabetically; 'feat' entries come first
    by convention.
    """
    groups: dict[str, list[ChangelogEntry]] = {}
    for entry in entries:
        groups.setdefault(entry.entry_type, []).append(entry)
    return groups


def format_changelog(changelog: Changelog) -> str:
    """
    Format a Changelog as a human-readable markdown string.

    Groups entries by type; each entry shows PR number, scope, description.
    """
    lines: list[str] = [
        f"# Changelog",
        f"",
        f"Version: {changelog.version}",
        f"Generated: {changelog.generated_at}",
        f"Total entries: {changelog.entry_count}",
        f"",
    ]

    groups = group_entries_by_type(changelog.entries)

    type_order = ["feat", "fix", "docs", "test", "refactor", "perf", "ci", "build", "chore", "style", UNKNOWN_TYPE]
    ordered_types = [t for t in type_order if t in groups]
    remaining = sorted(t for t in groups if t not in type_order)
    ordered_types.extend(remaining)

    for entry_type in ordered_types:
        type_entries = groups[entry_type]
        lines.append(f"## {entry_type.capitalize()}")
        lines.append("")
        for e in type_entries:
            sha_short = e.commit_sha[:7] if len(e.commit_sha) >= 7 else e.commit_sha
            lines.append(
                f"- **#{e.pr_number}** [{e.scope}] {e.description} "
                f"({e.merge_date[:10] if e.merge_date else ''})"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_changelog(
    version: str,
    generated_at: str,
    entries: list[ChangelogEntry],
) -> Changelog:
    """Build a Changelog from a list of ChangelogEntry instances."""
    return Changelog(
        version=version,
        generated_at=generated_at,
        entries=entries,
        entry_count=len(entries),
    )
