# Maintainer FAQ

## How do I merge a PR?
1. Ensure all checks pass.
2. Request review from at least one other maintainer for non-trivial changes.
3. Squash-merge with a descriptive commit message.
4. Delete the branch after merging.

## How do I create a release?
1. Complete the release readiness checklist.
2. Create a release branch.
3. Run `make full-reproducibility-report`.
4. Tag the release and publish release notes.

## How do I handle a safety issue?
1. Immediately flag the issue in the decision log.
2. Notify the project lead.
3. If needed, revert the unsafe change.
4. Document the resolution.
