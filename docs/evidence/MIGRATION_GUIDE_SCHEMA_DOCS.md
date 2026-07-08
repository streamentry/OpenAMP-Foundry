# Migration Guide: Schema Docs

When a schema changes or a new schema is added:

1. Update `schemas/` with the new or changed schema file.
2. Update `docs/engineering/SCHEMA_REGISTRY.md`.
3. Update any docs that reference the old schema path.
4. Run validation tests to confirm the schema is valid.
