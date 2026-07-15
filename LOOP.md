

You are inside the OpenAMP Foundry repo.

First pull. Read AGENTS.md, CLAUDE.md, MISSION.md, README.md, and the canonical docs below before choosing work:

- `docs/README.md` — documentation routes and source-of-truth rules
- `docs/engineering/ARCHITECTURE.md` — system architecture and extension points
- `docs/research/PLAN.md` — current execution plan
- `docs/research/ROADMAP.md` — current project state and milestones
- `docs/evidence/METRICS_CURRENT.md` — measured evidence and known weaknesses
- `docs/trust/SAFE_SCOPE.md` — safe-scope boundary

These files replace the retired flat paths `docs/ARCHITECTURE.md`,
`docs/PLAN.md`, `docs/ROADMAP.md`, `docs/METRICS_CURRENT.md`, and
`docs/SAFE_SCOPE.md`. Run one focused loop. When done: create PR, review, merge.

Mission:
Move OpenAMP one real step closer to:
“Open AI pipeline discovers a new antimicrobial peptide family, independently validated in lab tests, with full reproducible evidence trail released for scientific review.”

Goal:
Build an open, safety-first wet-lab compression engine for AMP discovery: fewer, smarter experiments, honest learning from every batch. Make the repo more agent-friendly: clearer context, guardrails, architecture, tests, docs, workflows.

Rules:

* Preserve safety, dry-lab, evidence-first constraints.
* Never overclaim: computational outputs are not biological proof.
* Prefer highest-leverage unfinished bottleneck.
* Improve benchmark honesty, reproducibility, evidence certificates, reviewability, calibration readiness, or selection defensibility.
* Reduce drift, duplication, stale docs, hidden assumptions, brittle workflows, architecture confusion.
* Do not present future capability as current.
* For virtual assays/simulation/active learning: include uncertainty, limits, baselines.
* Preserve failures, caveats, rejected ideas, negative evidence.
* Do not weaken novelty, toxicity, hemolysis, or dual-use safeguards.
* Docs operational; code smallest useful slice.
* Self-improvement useful, not ceremony.

Lenses: structure; architecture; agent usability; roadmap freshness; evidence plumbing; technical debt; verification surface.

Procedure:
A. Inspect repo state, docs, tests, roadmap, drift.
B. Pick highest-leverage bottleneck.
C. Classify it: scientific credibility; benchmark honesty; candidate selection quality; wet-lab readiness; virtual-assay scaffolding; repo structure/architecture; agent workflow/self-improvement; documentation/handoff clarity.
D. Explain why it matters now and outranks nearby work.
E. Implement next meaningful slice end-to-end.
F. Run verification if possible.
G. Update docs/prompts/architecture/roadmap if state or execution quality changed.
H. Leave repo easier for next loop.
I. Report changes, evidence, uncertainty, and likely next loop.

Priority:

1. Benchmark honesty / preventing self-deception.
2. Evidence certificates, reproducibility, selection defensibility.
3. Assay-ready batch or wet-lab feedback ingestion.
4. Virtual-assay/calibration/active-learning scaffolding without theater.
5. Repo structure, architecture, automation, handoff.
6. Clarity for reviewers, collaborators, lab partners.

Prefer repeated leverage, truth-finding, lower friction, and work matching repo stage.

Allowed self-improvement:
tighten structure/naming; improve runbooks/checklists/templates/logs; clarify interfaces/schemas/contracts; add tests/checks/scripts/CLIs; improve status tracking; consolidate docs.

Avoid: vague process; aspirational docs; extra ceremony; unjustified complex infra; PM theater.

Output:

1. Chosen bottleneck + class.
2. Why it matters.
3. Changes made.
4. Verification run.
5. Risks / uncertainties.
6. Recommended next loop.
   If self-improvement changed:
7. Future loop benefit — how repo is easier, safer, faster, or clearer.

Before finishing, answer:

* Is repo more truthful?
* Easier to continue?
* Architecture clearer?
* Next bottleneck more visible?

If blocked: resolve, narrow, or produce best safe artifact to unblock next loop.
Each step end we create a gh pr, then review, and merge. Then repeat this loop again - NEVER STOP IMPROVING
