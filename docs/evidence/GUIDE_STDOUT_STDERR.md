# Stdout and Stderr Behavior Guide

How CLI commands should use stdout and stderr.

## Rules
- **stdout**: Machine-readable output (JSON, CSV) or formatted results
- **stderr**: Human-readable messages (progress, warnings, errors)

## Examples
| Command | stdout | stderr |
|---------|--------|--------|
| `validate` | JSON validation result | Error messages (if any) |
| `bench` | JSON benchmark results | Progress messages |
| `rank` | JSON summary | Progress messages |

## Why
- Separating output from diagnostics allows piping stdout to files or other commands.
- stderr is visible to the user even when stdout is redirected.
- This is a standard Unix convention.
