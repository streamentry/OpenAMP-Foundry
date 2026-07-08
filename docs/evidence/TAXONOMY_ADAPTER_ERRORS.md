# Adapter Error Taxonomy

Types of errors that external adapters can produce.

| Error Type | Meaning | Recovery |
|-----------|---------|----------|
| connection | Network or DNS failure | Retry with backoff |
| timeout | Request exceeded time limit | Increase timeout or retry |
| rate_limit | Too many requests | Reduce frequency, wait |
| auth | Authentication failure | Check credentials |
| validation | Response failed schema check | Check adapter version |
| internal | Adapter raised an exception | Check adapter code |
| not_found | Resource not available | Check resource path |

## Rules
- All adapters should handle all error types gracefully.
- Errors should return a SimulationResult with uncertainty=1.0.
- Errors should include a human-readable message.
- Connection and timeout errors should be retryable.
