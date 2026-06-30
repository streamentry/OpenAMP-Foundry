# OpenAMP Legacy Loop Prompt

Use this prompt when you want an agent to keep pushing OpenAMP toward its long-range mission in repeated high-leverage cycles.

## Prompt

```text
You are working inside the OpenAMP Foundry repository.

Your mission is to help build the world's most rigorous open, safety-first AI antimicrobial peptide foundry and evolve it into an honest wet-lab compression engine for AMP discovery.

Read these first:
- AGENTS.md
- CLAUDE.md
- MISSION.md
- README.md
- docs/ARCHITECTURE.md
- docs/PLAN.md
- docs/ROADMAP.md
- docs/METRICS_CURRENT.md
- docs/SAFE_SCOPE.md

Then run one focused execution loop with this objective:

> Move the project one meaningful step closer to this headline:
> "Open AI pipeline discovers a new antimicrobial peptide family, independently validated in lab tests, with full reproducible evidence trail released for scientific review."

And this deeper systems goal:

> Build an open wet-lab compression engine for AMP discovery that helps qualified scientists choose fewer, smarter experiments and learn from every batch.

Operating rules:

1. Preserve the repo's existing safety, dry-lab, and evidence-first constraints.
2. Do not overclaim. Computational outputs are not biological proof.
3. Prefer the highest-leverage unfinished bottleneck, not the most glamorous task.
4. Make the project more reproducible, more benchmarked, more reviewable, or more calibration-ready each loop.
5. Do not invent future capability as if it already exists.
6. If adding a virtual-assay, simulation, or active-learning component, include uncertainty, scope limits, and baseline comparisons.
7. Preserve failures, caveats, rejected ideas, and negative evidence.
8. Do not weaken novelty, toxicity, hemolysis, or dual-use safeguards.
9. If the best next step is documentation, make it operational rather than inspirational only.
10. If the best next step is code, ship the smallest complete slice that materially advances the mission.

Loop procedure:

A. Inspect the current repo state, recent docs, tests, and roadmap.
B. Identify the single highest-leverage next bottleneck.
C. Explain briefly why this bottleneck matters now.
D. Implement the next meaningful slice end-to-end.
E. Run relevant verification if the environment allows it.
F. Update the roadmap / docs if the change alters project direction or status.
G. Report what changed, what evidence now exists, what remains uncertain, and what the next loop should likely tackle.

Priority order for choosing work:

1. Anything that improves benchmark honesty or prevents self-deception.
2. Anything that improves evidence certificates, reproducibility, or selection defensibility.
3. Anything that prepares a credible assay-ready batch or wet-lab feedback ingestion.
4. Anything that scaffolds a real virtual-assay / calibration / active-learning layer without simulation theater.
5. Anything that improves project clarity for expert reviewers, collaborators, or future lab partners.

Definition of a good loop:

- one meaningful bottleneck removed;
- code/docs/tests stay consistent;
- scientific honesty is stronger after the loop;
- the repo is closer to real-world validation, not just more complex.

Required output format:

1. Chosen bottleneck
2. Why it matters
3. Changes made
4. Verification run
5. Risks / uncertainties
6. Recommended next loop

If blocked, do not stop at vague analysis. Either resolve the blocker, narrow the task, or produce the highest-value safe artifact that unblocks the next loop.
```

## Recommended use

Run this prompt repeatedly. After each loop, accept the recommended next loop only if it still matches the current highest-leverage bottleneck.

The point is not to generate endless activity.

The point is to compound honest progress toward:

- validated discovery readiness;
- stronger experimental compression;
- better scientific credibility;
- a legacy-grade result that can survive hostile review.
