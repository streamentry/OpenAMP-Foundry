# Misuse Scenarios and Mitigations

Potential misuse scenarios and how the project mitigates them.

| Scenario | Risk | Mitigation |
|----------|:----:|------------|
| Overclaiming computational results as biological proof | High | `check_claims.py`, review process, AGENTS.md rules |
| Using pipeline to design toxins | High | No toxicity optimization, safety penalties, safety review |
| Releasing unscreened candidate lists | Medium | Gate process, human review, embargoed release |
| Misinterpreting safety scores as guarantees | Medium | LIMITATIONS_OVERVIEW.md, disclaimer in all outputs |
| Using pipeline without understanding limitations | Low | Honest limitations documented, quickstart guides |

## Principles
- Mitigations must not rely on users reading all documentation.
- Safety-relevant mitigations should be enforced by code or process.
- When code cannot prevent misuse, documentation and review must.
