# Secret-Scan Policy for Fixtures and Docs

Fixtures and documentation must not contain secrets.

## What to Scan For
- API keys (`sk-...`, `api_key=...`)
- Passwords (`password=...`)
- Tokens (`token=...`, `auth=...`)
- Private keys (`-----BEGIN...`)
- Connection strings (`mongodb://...`, `postgres://...`)

## Rules
- All fixtures and examples are scanned before commit.
- If a secret is found, remove it and rotate if it was ever committed.
- Use environment variables for any required credentials.
- The `.env` file is git-ignored.

## Enforcement
- Add secret scanning to CI (e.g., `trufflehog` or `git-secrets`).
- PRs that add new fixtures should be reviewed for secrets.
