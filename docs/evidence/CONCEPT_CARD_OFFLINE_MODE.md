# Offline Mode — Concept Card

Offline mode means running checks and validations without network access.

## Which Tools Support Offline Mode

| Tool | Offline? | Notes |
|------|:--------:|-------|
| `check_doc_links.py` | Yes | No network calls |
| `check_claims.py` | Yes | Local pattern matching |
| `check_pyproject.py` | Yes | Local file checks |
| `validate_negative_archive.py` | Yes | Local CSV validation |
| `validate_panel_csv.py` | Yes | Local CSV validation |
| `check_wave1_pass_fail.py` | Yes | Local JSON validation |
| `detect_unused_scripts.py` | Yes | Local file scanning |

## Rules

- All local checks must work without network access.
- Any tool requiring network access must document this requirement.
- CI runs with network access; local development should not require it.
