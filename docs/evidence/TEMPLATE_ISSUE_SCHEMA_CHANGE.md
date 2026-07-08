# Issue Template for Artifact Schema Changes

Template for issues that propose schema changes.

```markdown
## Summary
Brief description of the proposed schema change.

## Current Schema
Link to current schema file and relevant fields.

## Proposed Change
What fields are being added, removed, or changed.

## Rationale
Why this change is needed.

## Backward Compatibility
- Is this change backward-compatible?
- If not, what is the migration plan?

## Affected Artifacts
List all artifacts that use this schema.

## Related
- Link to related PRs or discussions.
```

## Rules
- Schema changes require maintainer review.
- Breaking schema changes require a migration plan.
- New fields should be optional when possible.
