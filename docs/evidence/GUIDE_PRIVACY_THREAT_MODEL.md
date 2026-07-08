# Artifact Privacy Threat Model

Potential privacy threats related to pipeline artifacts.

| Threat | Risk | Mitigation |
|--------|:----:|------------|
| Candidate sequences in logs | Low | Logs are local-only |
| Lab results contain PII | Medium | Lab partner agreement, data return schema excludes PII |
| Evidence certificates shared without context | Low | All certs include disclaimer |
| Manifest reveals internal paths | Low | Paths are relative, no user info |

## Principles
- Pipeline outputs should not contain PII.
- If PII is present, it must be clearly labeled and handled per data governance policy.
- All artifacts include a disclaimer stating they are computational predictions.
- Artifacts shared externally should be reviewed for sensitive content.
