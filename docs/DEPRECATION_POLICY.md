# Deprecation Policy

This document makes obsolescence intentional rather than accidental in the OpenAMP Foundry repository.

An undocumented deprecation is an invisible dependency. When something stops working and no one left a note, the cost is paid by the next contributor, not the one who made the change.

## Scope

This policy applies to:

- **Benchmark cards** (BMC- entries in `benchmark_registry.py`)
- **Evidence schemas** (Python dataclass modules in `src/openamp_foundry/evidence/`)
- **JSON schemas** (files in `schemas/`)
- **Scripts** (files in `scripts/`)
- **CLI commands** (subcommands in `src/openamp_foundry/cli/`)
- **Scoring modules** (files in `src/openamp_foundry/scoring/`)
- **Calibration modules** (files in `src/openamp_foundry/calibration/`)

## When to Deprecate

Deprecate rather than delete when:

1. **Something else does it better.** A new schema supersedes an old one, but old artifacts may still reference the old schema by name.
2. **A benchmark is no longer honest.** A benchmark whose results cannot be trusted should not silently disappear — it should be marked deprecated with a reason.
3. **A script produces stale output.** A script whose outputs are replaced by a newer pipeline stage should be deprecated, not deleted.
4. **A calibration module was replaced.** Old calibration logic should be deprecated before removal so audit trails remain readable.

Do not deprecate when:
- The artifact was never used in a commit that reached main.
- The artifact is a pure test helper with no external dependents.
- The change is a rename during the same PR (rename, don't deprecate-then-recreate).

## How to Deprecate

### Benchmark Cards (BMC-)

1. In `benchmark_registry.py`, set `deprecated=True` and `deprecation_notes` to the reason and the replacement.
2. Run `make bench-deprecation-check` — it must report the card as deprecated and not raise an error.
3. Deprecated cards MUST NOT appear in any active ranking call. `check_no_deprecated_in_ranking()` enforces this.
4. Leave the card in the registry for at least one release cycle before removal.

Example:
```python
BenchmarkCard(
    bmc_id="BMC-0002",
    ...
    deprecated=True,
    deprecation_notes="Replaced by BMC-0005 (charge-matched). See PR #412.",
)
```

### Evidence Schemas (Python modules)

1. Add a module-level deprecation notice at the top of the file:
   ```python
   # DEPRECATED since vX.Y.Z. Replaced by <new_module>. Do not use for new artifacts.
   ```
2. Keep the module importable — do not delete it immediately.
3. Add the old module name to the `DEPRECATED_SCHEMAS` list in `benchmark_deprecation.py` or equivalent.
4. Remove after one release cycle, once all callers are migrated.

### JSON Schemas

1. Add `"deprecated": true` and `"deprecation_reason"` to the schema's top-level properties.
2. Update `schemas/SCHEMA_CHANGELOG.md` (if present) with the deprecation notice.
3. Do not change the `$id` — existing artifacts reference the schema by ID.

### Scripts

1. Add a notice to the script header:
   ```python
   # DEPRECATED: use <replacement_script>.py instead. This script will be removed in vX.Y.
   ```
2. Do not remove the script until all documented workflows are updated.
3. If the script is referenced in any Makefile target, update or remove the target in the same PR.

### CLI Commands

1. Print a deprecation warning when the command is invoked:
   ```python
   import warnings
   warnings.warn("This command is deprecated. Use `openamp <new-command>` instead.", DeprecationWarning)
   ```
2. Keep the command functional for one release cycle.
3. Remove in the next release.

## Deprecation Timeline

| Phase | Duration | What happens |
|-------|----------|-------------|
| Deprecated | Current release | Marked, warning emitted, still works |
| Scheduled removal | Next release | Removal date announced in CHANGELOG |
| Removed | Following release | Gone; import raises ImportError or file is deleted |

The minimum deprecation window is **one release cycle** (one tagged version). Emergency removals (security, dual-use risk) may skip the window with a documented decision log.

## Communicating Deprecations

When deprecating an artifact:

1. **PR description**: State what is deprecated, why, and what replaces it.
2. **CHANGELOG entry**: Use the `chore: deprecate <name>` format.
3. **Decision log** (optional): For benchmark card or schema deprecations that affect the evidence chain, leave a decision log at `decision_logs/` (see `decision_logs/INDEX.md`).

## Anti-patterns

The following are deprecation failures:

| Anti-pattern | What it looks like | Why it fails |
|---|---|---|
| Silent deletion | File removed with no warning | Callers break at import; no migration path |
| Deprecation without reason | `deprecated=True` but no `deprecation_notes` | Future agents can't tell why it was deprecated |
| Dead benchmark revived | A deprecated BMC- card re-enabled without review | `make bench-deprecation-check` should catch this |
| Indefinite deprecation | Artifact stays deprecated for years | Signals confusion about ownership; remove or un-deprecate |

## Agents and Deprecation

An agent MUST NOT:
- Silently delete a module, schema, or benchmark card.
- Un-deprecate a benchmark card without human review.
- Change a schema `$id` or rename a BMC- card ID (this breaks existing artifact references).

An agent MAY:
- Propose a deprecation in a PR, following this policy.
- Add `deprecated=True` to a benchmark card, with `deprecation_notes` explaining why.
- Remove a script that was marked deprecated in a prior PR and whose removal was announced in the CHANGELOG.

When in doubt, deprecate rather than delete. Deletion is irreversible; deprecation is not.
