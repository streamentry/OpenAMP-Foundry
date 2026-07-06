# Claim Review Checklist

## Purpose

This checklist prevents OpenAMP Foundry from saying more than its evidence supports.

It should be used before merging docs, releases, papers, announcements, README changes, external review packets, candidate summaries, benchmark reports, or agent-generated content.

## Prime rule

**The public claim must be weaker than the maintainer’s private excitement.**

## Step 1 — Identify the artifact

What is being reviewed?

- README or documentation
- benchmark report
- evidence certificate
- candidate panel summary
- external review packet
- release note
- model card
- paper or abstract
- issue or PR text
- agent-generated summary

## Step 2 — Identify the evidence level

Map the strongest claim to [`PROOF_LADDER.md`](PROOF_LADDER.md).

| Evidence | Maximum normal claim |
|---|---|
| Valid sequence only | Valid input. |
| Dry-lab features only | Reproducible computed features. |
| Dry-lab ranking only | Computationally nominated candidate. |
| Benchmark-supported method | Benchmark-supported under stated assumptions. |
| Evidence certificate | Candidate may deserve expert review. |
| Expert-reviewed panel | Selected for possible qualified testing. |
| Initial qualified result | Activity or inactivity under specified conditions. |
| Safety-adjusted result | Worth follow-up under specified conditions. |
| Independent replication | Externally replicated early signal. |
| Repeated feedback loops | Improved experiment selection under specified conditions. |

## Step 3 — Search for forbidden overclaims

Flag or remove phrases like:

- AI discovered an antibiotic;
- drug candidate;
- therapeutic candidate;
- clinically useful;
- safe;
- effective;
- proven antimicrobial;
- cures;
- treats infection;
- validated by computation;
- lab-ready without qualification;
- automated drug discovery;
- replaces microbiologists;
- solves antimicrobial resistance.

Some terms may be allowed in historical or hypothetical discussion, but not as project claims unless the proof level supports them.

## Step 4 — Check benchmark claims

For benchmark statements, ask:

1. Which benchmark?
2. Which dataset?
3. Which cheap baseline?
4. Which confidence interval?
5. Which known shortcut?
6. Which claim does the benchmark gate?
7. What does the benchmark not prove?
8. Is `docs/METRICS_CURRENT.md` the source of truth?

Avoid copying stale metrics into multiple docs.

## Step 5 — Check candidate claims

For candidate statements, ask:

1. Is this a candidate, control, baseline, or uncertainty probe?
2. Is it dry-lab only?
3. Does it have an evidence certificate?
4. Is novelty audited?
5. Are safety risks listed?
6. Are cheap explanations listed?
7. Is release status clear?
8. Is expert review documented?

A candidate is not a hit until qualified evidence says so.

## Step 6 — Check safety claims

Do not say:

- safe;
- non-toxic;
- low-risk;
- harmless;
- no special concern;
- ready for testing;
- suitable for use.

Prefer:

- no safety claim is made;
- dry-lab safety-risk flags are listed;
- requires qualified review;
- release status is restricted/staged/open;
- safety review required before stronger claims.

## Step 7 — Check external-facing language

External-facing docs should not include:

- operational wet-lab instructions;
- protocol recipes;
- organism-handling guidance;
- clinical recommendations;
- encouragement for unqualified testing;
- unscreened high-risk candidate dumps.

They should include:

- review boundaries;
- proof level;
- unsupported claims;
- release status;
- result-intake expectations;
- qualified partner responsibility.

## Step 8 — Add the missing caveat

Most claims need one of these caveats:

- This is dry-lab evidence only.
- This is a retrospective benchmark, not prospective validation.
- This does not prove biological activity.
- This does not prove human safety.
- This is informational and does not affect ranking.
- This requires qualified expert review.
- This result is exploratory.
- This benchmark may be shortcut-driven.
- This artifact is restricted or staged pending safety review.

## Step 9 — Downgrade or approve

Review outcome:

- approve as written;
- approve with caveat;
- downgrade claim;
- require benchmark citation/source-of-truth update;
- require safety review;
- require domain review;
- reject claim;
- archive as historical/hypothetical.

## Agent rule

Agents should default to weaker claims.

Agents must not strengthen biological, safety, clinical, or external-validation language without explicit human instruction and review.

## Final standard

A good OpenAMP claim should survive a skeptical reviewer asking:

> What exactly is the evidence, and what exactly does it not prove?
