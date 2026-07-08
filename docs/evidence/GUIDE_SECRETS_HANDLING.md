# Secret-Handling Warning Page

OpenAMP Foundry does not handle secrets, credentials, or tokens.

## What We Do NOT Store
- API keys
- Passwords
- Tokens
- Certificates
- Any authentication material

## If You Need Secrets
Secrets for external services (e.g., predictor APIs) must be handled outside
the pipeline. Use environment variables or a secrets manager.

## Safety Rules
1. Never commit secrets to the repository.
2. Never hard-code credentials in scripts or adapters.
3. Use environment variables for any required authentication.
4. Document which environment variables are needed in the adapter docs.
5. The `.env` file is git-ignored; use it for local development.
