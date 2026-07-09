# Security Policy

## Purpose

This document describes how to report security vulnerabilities in the OpenAMP Foundry project privately, what the project maintains as its security boundary, and how reports are handled.

**Scope:** Computational code, Python library, CLI, schemas, documentation. This project is dry-lab only — there are no wet-lab protocols, clinical systems, or patient data.

---

## Reporting a Vulnerability

**Do NOT file a public GitHub issue for security vulnerabilities.**

Instead, report privately via one of these channels (in priority order):

1. **GitHub Private Vulnerability Reporting** — use the "Report a vulnerability" button on the GitHub Security tab.
2. **Maintainer email** — send to the primary maintainer (see MAINTAINER_ROTATION_PLAN.md for the current handle; find their contact via their GitHub profile).

Include in your report:
- Description of the vulnerability
- Steps to reproduce (minimal example preferred)
- Affected version(s) or commit hash
- Potential impact assessment
- Whether you have a proposed fix

---

## What Counts as a Security Issue

| Category | In scope | Examples |
|---|---|---|
| Code vulnerabilities | Yes | Command injection via CLI args, path traversal, insecure deserialization |
| Secret leakage | Yes | API keys, tokens, or credentials committed to the repo |
| Dependency vulnerabilities | Yes | Known CVEs in pinned dependencies that affect users |
| Overclaiming / false biological claims | Yes | Code that removes dry-lab-only guardrails or inflates evidence level |
| Dual-use safety safeguards | Yes | Weakening toxicity, hemolysis, or novelty checks without review |
| Missing features / performance | No | Feature requests and performance issues belong in public issues |
| Documentation inaccuracies | No | Minor doc fixes belong in public PRs |

---

## Response Timeline

| Step | Target |
|---|---|
| Acknowledgment | Within 48 hours of receipt |
| Initial assessment | Within 5 business days |
| Patch or mitigation | Within 30 days for confirmed high/critical issues |
| Public disclosure | After patch is available and reporter is notified |

If we cannot meet these timelines, we will communicate proactively.

---

## Severity Classification

| Severity | Description |
|---|---|
| Critical | Remote code execution, secret exposure, dry-lab boundary bypass |
| High | Privilege escalation, path traversal, dependency with known CVE |
| Medium | Denial of service (local CLI only), insecure default config |
| Low | Minor info disclosure, defense-in-depth improvements |

---

## Out of Scope

- Theoretical vulnerabilities without a reproducible proof of concept
- Issues that require physical access to the researcher's machine
- Social engineering attacks on maintainers
- Issues in dependencies where no fix is available upstream

---

## Process

1. Reporter files private report.
2. Maintainer acknowledges within 48 hours.
3. Maintainer assesses severity and determines whether fix is needed.
4. If confirmed: patch is developed on a private branch, reviewed, and merged.
5. A new release is cut with the fix.
6. Reporter is notified and given 7 days to review the fix before public disclosure.
7. Public disclosure is made via GitHub Security Advisory.

---

## Linked Policies

- [GOVERNANCE.md](../../GOVERNANCE.md)
- [SAFETY.md](../../SAFETY.md)
- [RESPONSIBLE_USE.md](../../RESPONSIBLE_USE.md)
- [MAINTAINER_ROTATION_PLAN.md](MAINTAINER_ROTATION_PLAN.md)
