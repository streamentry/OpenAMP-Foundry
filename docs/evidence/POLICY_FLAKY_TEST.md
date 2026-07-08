# Flaky Test Quarantine Policy

How flaky tests are handled.

## Definition
A flaky test is one that passes and fails without code changes.

## Process
1. Identify the flaky test and document the failure pattern in an issue.
2. If the test is low-value, remove it.
3. If the test is high-value, quarantine it by marking with `pytest.mark.flaky`.
4. Investigate the root cause within one sprint.
5. Fix or permanently remove the test.

## Quarantine Rules
- Flaky tests must not block CI.
- Quarantined tests should be tracked in a GitHub issue.
- Quarantined tests should be reviewed weekly.
- If a test remains flaky for more than 2 sprints, it should be removed.
