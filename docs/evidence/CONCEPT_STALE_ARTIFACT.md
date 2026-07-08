# Stale Artifact Concept Guide

An artifact is stale when it no longer reflects the current pipeline or data.

## Signs of Staleness
- Schema version doesn't match current code
- Benchmark results don't match current pipeline output
- Config values differ from the values used to generate the artifact
- The artifact references features or commands that no longer exist

## Causes
- Pipeline code updated without regenerating artifacts
- Schema changed without migrating existing artifacts
- Config changed without re-running dependent processes

## Prevention
- Regenerate artifacts after pipeline changes.
- Version schemas and check version alignment in CI.
- Run `make regenerate-all` before releases.
