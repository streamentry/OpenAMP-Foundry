# Test Runtime Budget Report

Reports how long tests take to run and flags slow tests.

## Current Status
Full test suite: ~80 seconds (varies by machine)

## Budget
| Test Category | Budget | Current |
|:-------------|:------:|:-------:|
| Unit tests | < 30s | ✅ |
| CLI tests | < 30s | ✅ |
| Integration tests | < 30s | ✅ |
| Full suite | < 120s | ✅ |

## Rules
- If a test consistently takes > 5s, mark it as slow.
- Slow tests should be optimized or moved to a separate CI job.
- Test runtime should be tracked in CI output.
- If the full suite exceeds 120s, investigate optimization.
