# Slow-Test Marker Policy

How to mark and handle slow tests.

## Marking
```python
@pytest.mark.slow
def test_expensive_operation():
    ...
```

## Running
```bash
# Skip slow tests
pytest -m "not slow"

# Only slow tests
pytest -m slow
```

## Rules
- Tests that take > 5s should be marked as slow.
- CI should run both slow and fast tests.
- Local development should default to skipping slow tests.
- Slow tests should be reviewed for optimization opportunities.
