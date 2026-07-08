# Tutorial Fixture Registry

All tutorial fixtures must be registered here.

| Fixture | Location | Used By |
|---------|----------|---------|
| Demo candidates | examples/sequences/demo_candidates.csv | QUICKSTART.md |
| Demo references | examples/known_reference/demo_known_amps.csv | QUICKSTART.md |
| Lab results (synthetic) | examples/lab_results/ | calibration walkthrough |
| Hemolysis reference | examples/validation/hemolysis_reference.csv | selectivity benchmark |

## Rules
- Add new fixtures to this registry when created.
- Mark fixtures as `synthetic` or `demo` in their metadata.
- Never use real candidate data as tutorial fixtures.
