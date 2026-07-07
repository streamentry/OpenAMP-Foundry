# Scenario Playbook: Stale Artifact Finding

**Scenario:** An artifact (schema, benchmark output, config) is stale and doesn't match the current code.

## Steps

1. Identify what's stale: check the artifact's schema version vs current code.
2. If the artifact is a benchmark output, regenerate it: `make bench-500`.
3. If the artifact is a schema, update it to match the current code.
4. If the artifact is a config file, update it or document why the discrepancy is acceptable.
5. Update any documentation that references the stale artifact.
6. Add a test to catch similar staleness in the future.

## Prevention

- Run `make regenerate-all` before major releases.
- CI should validate schema versions against code.
