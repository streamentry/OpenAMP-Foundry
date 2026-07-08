# Minimal Output Mode Guide

How to use minimal output mode for scripting and automation.

## Usage
Pass `--quiet` or set `LOG_LEVEL=WARNING` to reduce output.

## What's Included
- Errors and warnings only
- Final result summary (one line)

## What's Suppressed
- Progress messages
- Debug information
- Non-critical warnings

## Best Practices
- Use minimal mode in CI/CD pipelines.
- Use verbose mode (`--verbose`) when debugging.
- Default mode is appropriate for interactive use.
