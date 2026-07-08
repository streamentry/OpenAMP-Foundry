# Quiet Mode Policy for CLI Commands

CLI commands should support a quiet mode for scripting.

## Behavior
- `--quiet` flag suppresses all non-error output.
- Errors and the final result summary are still printed.
- Progress bars and informational messages are suppressed.

## Implementation
- Parse `--quiet` in the CLI handler.
- Set log level to WARNING when quiet is enabled.
- Suppress progress bars when quiet is enabled.

## Related
- `docs/evidence/GUIDE_MINIMAL_OUTPUT.md`
