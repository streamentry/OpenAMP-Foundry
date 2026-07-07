# Scenario Playbook: Changed Command Output

**Scenario:** A CLI command output format changes, potentially breaking downstream consumers.

## Steps

1. Determine if the change is intentional or accidental.
2. If intentional:
   - Update all documentation that references the old output format.
   - Update any tests that check the output format.
   - Add a changelog entry describing the change.
   - Consider backward compatibility or a migration path.
3. If accidental:
   - Fix the code to restore the expected output format.
   - Add a test to prevent future regressions.
4. Run the full test suite to verify no other code depends on the old format.
