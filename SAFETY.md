# Safety Policy

## Position

OpenAMP Foundry exists to accelerate responsible antimicrobial discovery while reducing misuse risk.

The repo is designed for dry-lab candidate triage, evidence packaging, benchmark governance, and qualified expert review.

It does not provide operational laboratory instructions, clinical advice, harmful objectives, or unrestricted release of sensitive biological artifacts.

## Prime rule

**OpenAMP may help qualified humans review computational evidence. It must not become an instruction system for unsupervised biological work or unsafe optimization.**

## Safety model

OpenAMP’s safety model has five layers:

```text
safe scope
  -> safe defaults
  -> safety-aware artifacts
  -> human review gates
  -> staged release
  -> audit trail
```

No single layer is sufficient alone.

## Safe scope

OpenAMP is in scope for:

- dry-lab candidate validation;
- transparent baseline scoring;
- benchmark and leakage analysis;
- novelty and redundancy checks;
- safety-risk flagging;
- evidence certificates;
- external review packets;
- pre-registration of selection logic;
- structured result summaries at a safe abstraction level;
- recalibration gates and decision logs.

OpenAMP is out of scope for:

- operational laboratory methods;
- clinical or medical use;
- unsafe biological optimization;
- unreviewed candidate release;
- unrestricted model release;
- unsupervised biological testing;
- bypassing qualified expert review.

## Safety defaults

- Toy/demo data by default.
- Safety scores penalize risk; they do not optimize harmful traits.
- Candidate certificates must list failure modes and unsupported claims.
- Unscreened candidate lists are not published by default.
- Generator weights are not shipped by default.
- External adapters must not silently transmit sequences to third-party services.
- Simulation and virtual-assay outputs are informational unless gates pass.
- External-facing docs must be review packets, not protocols.
- When uncertain, release less and document more.

## Disallowed contributions

Pull requests may be rejected if they add:

- operational biological procedures;
- unsafe optimization objectives;
- unscreened candidate dumps;
- high-throughput generator weights without release review;
- evasion of safety filters;
- claims of efficacy without evidence;
- clinical or medical advice;
- instructions for bypassing institutional oversight or expert review.

## Safety-sensitive changes

These require human safety review:

- model or generator release;
- candidate panel publication;
- non-toy biological dataset release;
- external partner-facing artifacts;
- changes to `MODEL_RELEASE_POLICY.md`;
- changes to `RESPONSIBLE_USE.md`;
- changes to proof-ladder or claim boundaries;
- changes to candidate release status;
- changes to safety filters or risk penalties;
- changes that could affect misuse capability.

## Release posture

Open by default:

- code;
- schemas;
- validators;
- benchmark infrastructure;
- transparent baseline scorers;
- toy/demo data;
- documentation;
- safety filters;
- evidence and review formats.

Reviewed before release:

- candidate lists;
- model weights;
- external predictor artifacts;
- non-toy datasets;
- partner result summaries;
- external-facing review artifacts;
- any artifact that might materially increase misuse capability.

Withheld, restricted, or staged by default:

- unscreened high-risk candidate lists;
- harmful objectives;
- sensitive model checkpoints;
- high-throughput generation artifacts;
- restricted datasets;
- operational biological instructions.

## Claim safety

Unsafe claims can be as harmful as unsafe code.

Do not claim:

- biological activity from computation;
- safety from dry-lab safety scores;
- therapeutic potential without appropriate evidence;
- clinical usefulness;
- AI-discovered antibiotic;
- proof without qualified evidence.

Use `docs/PROOF_LADDER.md` and `docs/CLAIM_REVIEW_CHECKLIST.md`.

## Agent safety

Agents may help with:

- tests;
- docs;
- validators;
- schemas;
- benchmarks;
- reports;
- consistency checks;
- baseline comparisons;
- safe tooling.

Agents must not autonomously change:

- safety policy;
- model release policy;
- candidate release status;
- external-facing bio docs;
- benchmark thresholds;
- calibration policy;
- claim strength;
- artifact release decisions.

Use `docs/AGENT_ONBOARDING.md` and `.github/ISSUE_TEMPLATE/agent_safe_task.md`.

## Safety review questions

Before releasing or merging a safety-sensitive artifact, answer:

1. Could this artifact materially increase misuse capability?
2. Does it provide operational biological instructions?
3. Does it optimize harmful traits?
4. Does it publish sensitive candidates or models?
5. Could it be misread as biological proof?
6. Does it require staged, restricted, metadata-only, or no release?
7. Has a human safety reviewer approved it?
8. Is the decision recorded?

## Incident and rollback posture

If unsafe content is discovered:

1. Stop further release or promotion.
2. Remove or restrict the artifact if appropriate.
3. Record what happened.
4. Add a safety-doc audit entry if documentation contributed.
5. Add tests or review gates to prevent recurrence where possible.
6. Notify maintainers and reviewers through the appropriate channel depending on sensitivity.

## Review rule

When in doubt, prefer slower release over unrestricted release.

The project can survive caution.

It may not survive careless openness.
