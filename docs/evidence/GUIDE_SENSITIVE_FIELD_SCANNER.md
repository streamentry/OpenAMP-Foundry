# Sensitive-Field Scanner for Generated Artifacts

Scans generated artifacts for potentially sensitive content.

## What to Scan
- Evidence certificates for PII in notes fields.
- Lab results for unexpected fields.
- Manifests for internal path information.
- Any generated file that will be shared externally.

## Patterns to Flag
- Email addresses
- IP addresses
- Internal file paths
- API keys or tokens
- Personal names (not in citations)

## Implementation
The scanner should be a script that reads a JSON or CSV file
and reports any lines that match sensitive patterns.

## Status
Proposed — not yet implemented.
