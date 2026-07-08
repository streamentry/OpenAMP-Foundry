# Adapter Timeout Policy

Timeout rules for external adapter calls.

## Default Timeouts
| Adapter Type | Default Timeout | Max Timeout |
|-------------|:---------------:|:-----------:|
| External API | 30 seconds | 120 seconds |
| Local process | 60 seconds | 300 seconds |
| File I/O | 10 seconds | 60 seconds |

## Rules
- Adapters should have configurable timeout values.
- Timeout errors should be retried at least once.
- If a timeout persists, return uncertainty=1.0.
- Document timeout behavior in each adapter's docstring.
- Timeouts should not block the pipeline — use async or thread-based timeout.
