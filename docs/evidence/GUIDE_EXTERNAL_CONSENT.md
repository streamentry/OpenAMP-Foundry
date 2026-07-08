# External-Access Consent Note

External adapters must not access network resources without explicit user consent.

## Consent Rules
1. Adapters must declare whether they require network access.
2. Network access must be opt-in, not opt-out.
3. Users must be informed before any data is sent externally.
4. The purpose of the external access must be documented.
5. No credentials may be stored or transmitted without explicit consent.

## Implementation
- Adapters should use `required_module` parameter in `ExternalSimulationAdapter`.
- Network-dependent adapters should document this in their class docstring.
- Local tests should not require network access.
