# Schema — Concept Card

A schema is a machine-readable definition of an artifact's structure.

## Schema Formats Used

| Format | Use | Validator |
|--------|-----|-----------|
| JSON Schema (Draft 2020-12) | Evidence certs, lab results, manifests | `openamp-foundry validate` |
| Python dataclass | Simulation results, scored candidates | Runtime type checking |
| YAML | Config files, pass/fail criteria | Application-level loading |

## Rules

- Every persistent artifact should have a schema.
- Schema changes must be backward-compatible or versioned.
- Schemas live in `schemas/`.

## Related

- `schemas/` — schema directory
- `docs/engineering/SCHEMA_REGISTRY.md` — schema registry
