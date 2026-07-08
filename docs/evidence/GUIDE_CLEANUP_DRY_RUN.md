# Generated Output Cleanup Dry-Run

Preview which generated files would be cleaned up.

## Usage
```bash
# Dry-run: list files that would be removed
ls outputs/*.json outputs/*.jsonl outputs/*.md 2>/dev/null

# Actual cleanup
rm -rf outputs/*.json outputs/*.jsonl outputs/*.md
```

## What Would Be Removed
- `outputs/*.json` — benchmark results, manifests
- `outputs/*.jsonl` — ranked candidate lists
- `outputs/*.md` — reports
- `outputs/evidence/` — evidence certificates (regenerable)

## What Would NOT Be Removed
- `outputs/.gitkeep` — keeps directory in git
- `outputs/lab_results/` — lab data (if present)

## Regeneration
After cleanup, regenerate with:
```bash
make demo
make regenerate-all
```
