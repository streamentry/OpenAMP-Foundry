# Change Note Writing Guide

How to write good change notes for PRs and releases.

## Structure

Each change note should follow this format:

```
- ``path/to/changed/file`` — Brief description of what changed and why.
```

## Examples

```
- ``src/openamp_foundry/pipeline.py`` — Added charge_bias score to candidate output.
- ``docs/evidence/LIMITATIONS_OVERVIEW.md`` — Added calibration limitations section.
```

## Rules

- Start with the file path in backticks.
- Use past tense for what was done.
- Include the reason if it's not obvious.
- Keep each entry to one line when possible.
- Group related changes together.
