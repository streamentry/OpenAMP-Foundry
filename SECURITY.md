# Security and Safety-Sensitive Reporting Policy

## Purpose

This document explains how to report software security issues, safety-sensitive content, credential exposure, private data exposure, and release-risk concerns.

OpenAMP Foundry is both a software project and a safety-constrained scientific infrastructure project. Some issues should not be opened publicly.

## Report privately

Report privately to maintainers when an issue involves:

- private credentials or tokens;
- private dataset access;
- partner or reviewer private information;
- sensitive candidate or model artifacts;
- unsafe release pathways;
- bypass of safety or release checks;
- content that could materially increase misuse risk;
- vulnerabilities in CI, packaging, or artifact publication.

Do not include sensitive details in a public issue.

## Public issues are appropriate for

Use normal GitHub issues for:

- installation bugs;
- failing tests;
- documentation errors;
- schema validation bugs;
- unclear CLI behavior;
- benchmark reproducibility problems that do not expose sensitive artifacts;
- safe feature requests.

Use the issue templates when possible.

## What not to post publicly

Do not open public issues containing:

- private keys, credentials, tokens, or URLs with secrets;
- restricted data;
- sensitive candidate lists;
- unreleased model artifacts;
- operational biological instructions;
- instructions for bypassing safety review;
- partner-private result details;
- exploit instructions beyond what maintainers need to understand impact.

## Maintainer response

For safety-sensitive reports, maintainers should:

1. Acknowledge receipt.
2. Restrict discussion to appropriate reviewers.
3. Assess whether immediate removal or restriction is needed.
4. Record a decision when safe to do so.
5. Add tests, gates, docs, or review requirements to prevent recurrence.
6. Publish a safe summary if public awareness is useful and safe.

## Coordinated disclosure

If an issue affects users, artifacts, or downstream consumers, maintainers should coordinate a fix and communicate clearly without exposing sensitive details.

## Related policies

- [`SAFETY.md`](SAFETY.md)
- [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md)
- [`MODEL_RELEASE_POLICY.md`](MODEL_RELEASE_POLICY.md)
- [`docs/trust/RELEASE_CHECKLIST.md`](docs/trust/RELEASE_CHECKLIST.md)
- [`docs/trust/SAFETY_DOC_AUDIT.md`](docs/trust/SAFETY_DOC_AUDIT.md)

## Final rule

When unsure whether an issue is safe to disclose publicly, report privately first.
