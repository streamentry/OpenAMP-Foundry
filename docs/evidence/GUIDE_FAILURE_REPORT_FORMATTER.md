# Failure Report Formatter for Local Checks

Formats failure reports from local validation checks.

## Output Format
```json
{
  "check": "check_doc_links",
  "status": "failed",
  "failed": 5,
  "passed": 95,
  "total": 100,
  "errors": [
    {"file": "docs/example.md", "error": "Broken link: PROOF_LADDER.md"}
  ],
  "suggested_actions": [
    "Fix the broken links in docs/example.md",
    "Run the check again to verify"
  ]
}
```

## Rules
- Failure reports should be machine-readable (JSON).
- Include the check name, status, and error details.
- Include suggested actions for fixing common errors.
- Reports should be written to `outputs/check_reports/`.
