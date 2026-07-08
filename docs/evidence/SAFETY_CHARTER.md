# One-Page Safety Charter

## Our Commitment
OpenAMP Foundry is a dry-lab computational project. It does not conduct
biological experiments. It does not provide protocols for handling
dangerous organisms. It does not optimize for toxicity or harmful outcomes.

## Safety Rules
1. No wet-lab protocols in this repository.
2. No optimization for mammalian toxicity.
3. No instructions for pathogen enhancement.
4. No release of unscreened high-risk candidate lists.
5. Human review required before any release or public claim.

## Enforcement
- `scripts/safety/check_claims.py` scans for overclaiming language.
- All PRs are reviewed for safety implications.
- Safety-critical changes require a designated safety reviewer.

## Related
- `SAFETY.md` — full safety policy
- `RESPONSIBLE_USE.md` — allowed and forbidden uses
