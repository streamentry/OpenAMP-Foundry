# Make Target Guide

How to use Makefile targets in the project.

## Common Targets
| Target | Purpose |
|--------|---------|
| `make demo` | Run the demo pipeline |
| `make test` | Run all tests |
| `make bench-500` | Run 500-AMP benchmark |
| `make bench-gate` | Check benchmark regression gates |
| `make regenerate-all` | Regenerate all outputs |
| `make full-reproducibility-report` | Generate release report |
| `make lab-batch-pack` | Build lab partner zip |

## Adding a New Target
1. Add the target to the Makefile.
2. Add it to the `.PHONY` list if it doesn't create a file.
3. Add a description to the help section.
4. Document the target in COMMAND_SURFACE.md if it's user-facing.
