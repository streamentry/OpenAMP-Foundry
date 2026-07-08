# Issue Batching Guide

How to batch related issues into efficient PRs.

## When to Batch

- Issues are in the same area of the codebase.
- Issues are small and independent.
- Issues have the same reviewer.

## When NOT to Batch

- Issues touch safety policy — keep separate.
- Issues have different priorities.
- Issues require different review expertise.

## Best Practices

- Limit batches to 10 issues per PR.
- List all closed issues in the PR description.
- Use "Closes #N, Closes #M" format.
- Ensure each issue has its own commit or clear scope in squashed commit.
