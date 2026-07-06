# Doctor command

`make doctor` is the quickest environment-readiness check for a fresh OpenAMP checkout.

It verifies only local setup basics:

- supported Python version;
- expected project files and directories;
- presence of helpful optional tools such as `git`, `ruff`, and `pytest`.

It does **not** run the scientific pipeline, validate evidence certificates, or support any biological claim.

Run:

```bash
make doctor
```

For machine-readable output:

```bash
python scripts/release/doctor.py --json
```

A passing doctor report means the checkout is probably ready for `make demo`, `make test`, and the getting-started walkthrough. It does not mean benchmark, safety, or review gates passed.
