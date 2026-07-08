# Walkthrough Expected-Output Snapshots

Walkthroughs should include expected output snapshots so users can verify
they got the right result.

## Format
```markdown
## Expected Output

After running `openamp-foundry rank ...`, the first line of the output file
should contain a JSON object with these keys:
- `candidate_id` — string
- `sequence` — string  
- `scores` — dict with at least `ensemble`, `activity`, `safety`
- `selected` — boolean
```

## Rules
- Show the structure, not exact values.
- If exact values are shown, mark them as examples.
- Update snapshots when output format changes.
