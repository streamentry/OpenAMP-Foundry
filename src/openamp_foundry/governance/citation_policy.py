"""Citation and reuse policy validation for OpenAMP Foundry artifacts."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

VALID_CITATION_TYPES: set[str] = {"dataset", "method", "schema", "software"}
VALID_REUSE_CLASSES: set[str] = {
    "attribution_required",
    "contact_required",
    "open",
    "restricted",
}
VALID_LICENSE_IDENTIFIERS: set[str] = {
    "Apache-2.0",
    "CC-BY-4.0",
    "CC-BY-NC-4.0",
    "MIT",
    "Proprietary",
}


@dataclass
class CitationEntry:
    """A single citable artifact entry."""

    artifact_id: str
    citation_type: str
    title: str
    version: str
    authors: List[str]
    year: str
    license_identifier: str
    reuse_class: str
    url: str = ""
    bibtex_key: str = ""
    dry_lab_only: bool = True


@dataclass
class CitationValidationResult:
    """Result of validating a CitationEntry."""

    artifact_id: str
    citation_type: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_citation_entry(entry: CitationEntry) -> CitationValidationResult:
    """Validate a CitationEntry against policy rules."""
    errors: list[str] = []
    warnings: list[str] = []

    if not entry.artifact_id or not entry.artifact_id.strip():
        errors.append("artifact_id must be non-empty")

    if entry.citation_type not in VALID_CITATION_TYPES:
        errors.append(
            f"citation_type must be one of {sorted(VALID_CITATION_TYPES)}, "
            f"got: {entry.citation_type!r}"
        )

    if not entry.title or not entry.title.strip():
        errors.append("title must be non-empty")

    if not entry.version or not entry.version.strip():
        errors.append("version must be non-empty")

    if not entry.authors:
        errors.append("authors must be a non-empty list")

    if not re.match(r"^\d{4}$", str(entry.year)):
        errors.append(
            f"year must be a 4-digit string (YYYY), got: {entry.year!r}"
        )

    if entry.license_identifier not in VALID_LICENSE_IDENTIFIERS:
        errors.append(
            f"license_identifier must be one of "
            f"{sorted(VALID_LICENSE_IDENTIFIERS)}, got: {entry.license_identifier!r}"
        )

    if entry.reuse_class not in VALID_REUSE_CLASSES:
        errors.append(
            f"reuse_class must be one of {sorted(VALID_REUSE_CLASSES)}, "
            f"got: {entry.reuse_class!r}"
        )

    if not entry.dry_lab_only:
        errors.append("dry_lab_only must be True for citation entries")

    if entry.reuse_class == "restricted":
        warnings.append(
            "reuse_class is 'restricted': contact maintainers before any reuse"
        )

    if entry.reuse_class == "contact_required" and not entry.url:
        warnings.append(
            "reuse_class is 'contact_required' but url is empty: "
            "provide a contact URL"
        )

    if not entry.bibtex_key:
        warnings.append(
            "bibtex_key is empty: provide a BibTeX key for easy citation"
        )

    return CitationValidationResult(
        artifact_id=entry.artifact_id,
        citation_type=entry.citation_type,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_citation_dict(d: dict) -> CitationValidationResult:
    """Validate a dict representation of a CitationEntry."""
    required = [
        "artifact_id",
        "authors",
        "citation_type",
        "license_identifier",
        "reuse_class",
        "title",
        "version",
        "year",
    ]
    missing = [f for f in required if f not in d]
    if missing:
        return CitationValidationResult(
            artifact_id=d.get("artifact_id", ""),
            citation_type=d.get("citation_type", ""),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )
    entry = CitationEntry(
        artifact_id=d["artifact_id"],
        citation_type=d["citation_type"],
        title=d["title"],
        version=d["version"],
        authors=d["authors"],
        year=str(d["year"]),
        license_identifier=d["license_identifier"],
        reuse_class=d["reuse_class"],
        url=d.get("url", ""),
        bibtex_key=d.get("bibtex_key", ""),
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_citation_entry(entry)
