# Scenario Playbook: Missing Schema Reference

**Scenario:** A document references a schema file that doesn't exist or is outdated.

## Steps

1. Check `schemas/` for the expected schema file.
2. If the schema exists but is outdated, update it to match the current data format.
3. If the schema doesn't exist, create it from the data format used in the code.
4. Update the document to reference the correct schema path.
5. Add a test that validates the schema exists and is valid.
6. Run `python -m openamp_foundry.cli validate` against existing data to verify.
