# First Successful PR Guide

Steps to get your first PR merged.

## Choose an Issue
Pick an issue labeled `good-first-issue`. These are small, well-scoped tasks.

## Set Up
```bash
git clone https://github.com/Open-Problem-Lab/OpenAMP-Foundry.git
cd OpenAMP-Foundry
git checkout -b your-branch-name
```

## Make Changes
1. Make your change.
2. Add or update tests.
3. Verify: `python3 -m pytest -q`
4. Verify: `python scripts/check_doc_links.py`

## Submit
```bash
git add -A
git commit -m "Brief description of the change"
git push origin your-branch-name
```
Then create a PR on GitHub referencing the issue number.

## After Submission
- Respond to review comments.
- Make requested changes.
- Once approved, your PR will be merged.
