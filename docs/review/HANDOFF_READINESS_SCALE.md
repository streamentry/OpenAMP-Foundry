# Handoff Readiness Scale

OpenAMP Foundry should distinguish exploratory dry-lab artifacts from artifacts that are ready for qualified external review.

This scale defines evidence readiness for handoff packets without adding wet-lab protocols, operational methods, candidate-generation instructions, or optimization objectives.

## Readiness levels

| Level | Name | Meaning |
|---|---|---|
| H0 | exploratory | Useful for internal learning only. Not ready for external review. |
| H1 | structured | Artifact is valid, reproducible, and documented, but major evidence gaps remain. |
| H2 | reviewable | Artifact has enough provenance, baseline comparison, limitations, and safety boundaries for expert review. |
| H3 | bounded review | Expert review may proceed only inside a clearly narrowed scope. |
| H4 | handoff ready | Artifact is suitable for qualified external review under the documented claim boundary. |
| H5 | returned evidence | External review or result has returned and must update the evidence record. |

No level means biological efficacy is proven.

## Minimum handoff readiness note

```markdown
## Handoff readiness

**Artifact:** Evidence certificate, shortlist, report, or review packet.

**Readiness level:** H0 | H1 | H2 | H3 | H4 | H5.

**Reason:** One paragraph.

**Required evidence present:** Provenance, run manifest, baseline comparison, leakage audit, limitations, safety boundary, reviewer route.

**Missing evidence:** What prevents the next level?

**Allowed use:** Internal learning | maintainer review | expert review | bounded external review | update from returned evidence.

**Not allowed:** What this artifact must not be used to claim.
```

## Promotion guidance

Promote readiness only when the artifact becomes safer and more reviewable, not merely more impressive.

An H4 artifact must have:

- clear provenance;
- reproducible generation path;
- declared claim boundary;
- baseline comparison when model-like components are involved;
- leakage audit when evaluation is involved;
- limitations and failure modes;
- reviewer routing;
- explicit statement of what is not claimed.

## Reviewer guidance

Reviewers should use the scale to avoid binary thinking.

A packet may be good work and still only H1 or H2. That is not failure. It is honest status.

## Agent guidance

Agents should propose a readiness level before requesting external review.

If an agent cannot say what evidence is missing for the next level, the artifact is not ready to leave internal review.

## Acceptance test

The readiness label is useful when a maintainer can answer:

1. Who may review this artifact?
2. What evidence is present?
3. What evidence is missing?
4. What claim boundary travels with it?
5. What must not be claimed from it?
