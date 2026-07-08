# Adapter Privacy Checklist

Privacy checklist for external adapters.

## Checklist
- [ ] Adapter declares whether network access is required.
- [ ] No data is sent without user consent.
- [ ] Adapter does not collect telemetry.
- [ ] Credentials are not stored in code.
- [ ] Authentication uses environment variables or secure storage.
- [ ] Data sent to external services is documented.
- [ ] Users are informed before any network request is made.

## Rules
- All adapters must pass this checklist before being used with real data.
- Adapters that fail the checklist may only be used with synthetic data.
- This checklist should be reviewed when adding new adapters.
