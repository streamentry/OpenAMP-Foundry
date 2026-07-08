# Decision Record Template Validator

Validates decision log entries against the schema.

## Usage
```bash
python -m openamp_foundry.cli validate \
  --certificate decision_log_entry.json \
  --schema schemas/decision_log.schema.json
```

## Checks
The schema validates:
- Required fields are present
- Decision type is one of the allowed values
- Decision is approved, rejected, or deferred
- If dissent_flag is true, dissent_notes are required
- Date is in ISO 8601 format
