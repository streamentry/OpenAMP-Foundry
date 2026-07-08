# Repository Path Resolver Utility

Helper for resolving paths within the repository.

## Usage
```python
from pathlib import Path

def repo_path(*parts: str) -> Path:
    """Resolve a path relative to the repository root."""
    return Path(__file__).resolve().parent.parent / Path(*parts)

# Examples
candidates = repo_path("examples", "sequences", "demo_candidates.csv")
config = repo_path("configs", "pipeline.yaml")
```

## Rules
- Always resolve paths relative to the repository root, not the current working directory.
- Use `Path.resolve()` to handle symlinks and relative paths.
- Never hardcode absolute paths.
- Test paths should use `tmp_path` fixture where possible.
