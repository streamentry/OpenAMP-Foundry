# Issue Decomposition Guide

How to break large issues into manageable pieces.

## When to Decompose

- An issue is estimated to take more than one sprint.
- An issue touches multiple independent areas.
- An issue cannot be reviewed as a single PR.

## Decomposition Strategy

1. Identify the independent sub-tasks.
2. Create separate issues for each sub-task.
3. Link the sub-tasks to the parent epic.
4. Order the sub-tasks by dependency.
5. Assign each sub-task to a milestone.

## Example

Instead of one issue "Improve documentation," create:
- "Fix broken links in docs/"
- "Add concept cards for evidence types"
- "Update QUICKSTART.md for new CLI flags"
