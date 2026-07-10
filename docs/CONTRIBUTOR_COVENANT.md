# Contributor Covenant and Attribution Policy

This document defines the standards for participation in the OpenAMP Foundry project and the policy for attributing contributions to the repository.

## Our pledge

We as contributors and maintainers pledge to make participation in OpenAMP Foundry a harassment-free experience for everyone, regardless of background, experience level, or affiliation. We pledge to act and interact in ways that contribute to an open, welcoming, and technically rigorous environment.

## Standards of conduct

### Expected behavior

- Use welcoming and inclusive language.
- Be respectful of differing viewpoints and experience.
- Gracefully accept constructive criticism.
- Focus on what is best for the project and its scientific integrity.
- Show empathy toward other contributors.
- Clearly separate computational outputs from biological claims in all discussions and documentation.

### Unacceptable behavior

- Harassment, trolling, derogatory comments, or personal attacks.
- Publishing private information about others without explicit permission.
- Overclaiming: presenting dry-lab computational results as biological proof in contribution discussions, PR descriptions, or issues.
- Deliberately weakening safety constraints, toxicity gates, hemolysis filters, or dual-use safeguards without explicit human review sign-off.
- Forging or misrepresenting evidence artifacts, benchmark results, or calibration records.
- Other conduct that a reasonable person would consider inappropriate in a professional scientific or software context.

## Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable behavior and are expected to take appropriate action in response to unacceptable behavior.

Maintainers have the right and responsibility to remove, edit, or reject contributions that do not align with this covenant, or to temporarily or permanently ban any contributor for behaviors they deem inappropriate, threatening, offensive, or harmful.

## Attribution policy

### What is attributed

All meaningful contributions are attributed. This includes:

- Code, schema, and test authorship (tracked automatically by git).
- Documentation writing.
- Benchmark design and critical review.
- Identified and documented failure modes.
- Disconfirming evidence that prevented a false positive.

### How attribution is recorded

1. **Git authorship.** Every commit records the author's name and email as configured in their git client. This is the primary attribution record.
2. **`CONTRIBUTORS.md`.** Major contributors (defined as ≥3 merged PRs or a significant architectural contribution) may add themselves to `CONTRIBUTORS.md` in any PR.
3. **Acknowledgment in evidence artifacts.** Evidence certificates and release manifests record the `pipeline_version` and commit SHA that produced them. Individual contributor attribution for specific pipeline runs belongs in the associated git history and PR description, not in the artifact itself.

### What is NOT attributed in artifacts

Evidence artifacts (CERT-, RMF-, BMC-, etc.) are pipeline outputs. They record the **software version and commit** that produced them, not the individual contributor's name. This separation is intentional:

- It prevents individual reputation from inflating or discounting an artifact's value.
- It keeps the artifact's scientific validity grounded in the reproducible pipeline, not in perceived expertise.
- It reduces the risk that a contributor's departure causes evidence to be re-evaluated for non-scientific reasons.

### AI and agent contributions

Automated agents (including Claude Code, opencode workers, and any other AI tools) may author code committed to this repository under human direction and review. The human who reviews and merges the agent's contribution is the responsible maintainer of record.

Agent-authored commits must not be attributed to a human as if the human wrote the code manually. Agent contributions are recorded in git with the agent's configured identity or with an explicit "Co-Authored-By" footer where the human accepts responsibility.

## Enforcement

Instances of unacceptable behavior may be reported by opening a confidential issue with the label `conduct` or by contacting the repository maintainers directly via the contact listed in the repository profile.

All complaints will be reviewed and investigated promptly. Maintainers are obligated to maintain confidentiality regarding the reporter of an incident.

Maintainers who do not follow or enforce this covenant may face temporary or permanent consequences determined by other members of the project's leadership.

## Attribution

This document is adapted from the [Contributor Covenant](https://www.contributor-covenant.org), version 2.1, available at https://www.contributor-covenant.org/version/2/1/code_of_conduct.html.

The attribution policy is specific to the OpenAMP Foundry project and its evidence-first, dry-lab-only scientific context.
