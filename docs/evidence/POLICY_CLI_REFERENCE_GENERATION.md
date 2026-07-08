# CLI Reference Generation Policy

CLI reference docs should be generated from the code, not written manually.

## Current State
CLI reference is maintained in docs/getting-started/COMMAND_SURFACE.md.

## Policy
- Add new commands to COMMAND_SURFACE.md when they are added.
- Update COMMAND_SURFACE.md when command flags change.
- Consider auto-generating the reference from argparse in the future.

## Related
- `docs/getting-started/COMMAND_SURFACE.md` — CLI reference
