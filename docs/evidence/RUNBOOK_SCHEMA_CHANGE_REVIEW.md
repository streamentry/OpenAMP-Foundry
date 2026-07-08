# Maintainer Runbook: Schema Change Review

When a schema changes:

1. Verify the new schema is valid JSON Schema.
2. Run validation tests against existing data.
3. Check if the change is backward-compatible (new optional fields are OK).
4. If breaking, update all consumers of the schema.
5. Update SCHEMA_REGISTRY.md.
6. Update any docs that reference the old schema.
7. Verify the reproducibility report still works.
