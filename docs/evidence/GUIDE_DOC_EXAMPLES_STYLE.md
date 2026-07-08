# Doc Examples Style Guide

How to write examples in documentation.

## Command Examples
- Use `bash` code blocks with `$` prefix for commands.
- Show the expected output format, not the exact output.
- Keep examples runnable from a clean checkout.

## Code Examples
- Use `python` code blocks for Python examples.
- Show only the relevant parts, not the entire file.
- Use comments to explain non-obvious behavior.

## Data Examples
- Use `csv` or `json` code blocks for data examples.
- Show only a few rows for CSV examples.
- Use realistic but clearly synthetic data.
- Mark synthetic data with a comment or note.

## Rules
- All examples must work from a clean checkout.
- Examples must not contain real candidate data.
- Examples must include a disclaimer if showing pipeline output.
