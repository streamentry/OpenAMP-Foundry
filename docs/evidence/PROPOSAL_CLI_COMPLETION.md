# CLI Completion Support Proposal

Adding shell completion support for the CLI.

## Motivation
Shell completion improves developer experience by showing available
commands, flags, and values.

## Approach
Use Python's `argparse` with `argcomplete` for shell completion.

## Required Changes
1. Add `argcomplete` as an optional dependency.
2. Add shell completion entry point in `pyproject.toml`.
3. Register argparse parsers with `argcomplete.autocomplete()`.
4. Document how to enable completion in the shell.

## Completion Types
- Command names: `rank`, `validate`, `bench`, etc.
- Flag names: `--candidates`, `--out`, `--config`, etc.
- File paths: for `--candidates`, `--out` flags.
- Enum values: for `--ranking-mode` (ensemble, expert).

## Status
Proposed — not yet implemented.
