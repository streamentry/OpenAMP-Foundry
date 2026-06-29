# Wave 0.5 — Scaffold Diversification Plan

## Purpose

OpenAMP currently has a strong pre-wet-lab AMP candidate package, but the candidate panel is still too correlated. Many candidates come from the same seed families, so if one scaffold fails because of mechanism, hemolysis, cytotoxicity, synthesis instability, or novelty/IP weakness, several related variants may fail together.

Wave 0.5 exists to increase the number of **independent biological bets** before Wave 1 wet-lab testing.

The goal is not to generate many more peptides. The goal is to build a better final Wave 1 panel with:

```text
more independent scaffold families
fewer redundant variants
better activity/safety balance
stronger novelty filtering
clear controls
clear go/no-go gates
```

---

## Current Situation

The current panel has 20 candidates from 7 seed families:

```text
SEED-001
SEED-003
SEED-005
SEED-006
SEED-007
SEED-008
SEED-009
```

Current interpretation:

| Seed     | Current Role                              | Notes                                                  |
| -------- | ----------------------------------------- | ------------------------------------------------------ |
| SEED-001 | Positive control only                     | Known/magainin-like; not novelty lead                  |
| SEED-003 | SAR/control only                          | Known-variant/tachyplesin-like; not novelty lead       |
| SEED-005 | Optional / low priority                   | Close-relative; useful but weak novelty                |
| SEED-006 | Primary balanced lead                     | Strongest current balance of activity and safety       |
| SEED-007 | Activity candidate / safety mixed         | Useful, but AntiCP/off-target concern                  |
| SEED-008 | High-upside / hemolysis risk              | Strong activity predictors, but HemoFinder high-risk   |
| SEED-009 | Mechanistically interesting / AntiCP risk | HemoFinder low, but AntiCP-positive/off-target concern |

Current external predictor stack:

```text
CAMPR4 / CAMP-style predictor
AMPScanner v2
Macrel
AMPActiPred
AntiCP2
HemoFinder
OpenAMP internal scoring
```

Current issue:

```text
The panel has decent predictor support, but too many candidates are family-correlated.
```

---

## Wave 0.5 Goal

Produce a new diversified candidate panel for Wave 1.

Target final panel:

```text
20–24 peptides total
10–12 independent scaffold families
1–2 candidates per lead family
2–4 controls
clear activity/safety/novelty evidence for every candidate
```

The final Wave 1 panel should maximize the chance of at least one useful wet-lab hit while reducing the chance that one family-level failure kills the whole batch.

---

## Non-Goals

Wave 0.5 must not do the following:

```text
Do not claim antimicrobial activity.
Do not claim clinical utility.
Do not claim “AI discovered an antibiotic.”
Do not provide public wet-lab protocols.
Do not optimize for toxicity, hemolysis, mammalian-cell killing, virulence, or pathogen enhancement.
Do not publish final lead sequences as commercial breakthroughs before IP/novelty review.
```

OpenAMP remains a dry-lab evidence and candidate-nomination system. Wet-lab truth must come from qualified collaborators.

---

## Success Criteria

Wave 0.5 is successful when the repo can produce:

```text
outputs/wave0_5_candidates.csv
outputs/wave0_5_external_consensus.csv
outputs/wave0_5_safety_consensus.csv
outputs/wave0_5_novelty_audit.csv
outputs/wave0_5_panel_selection.md
docs/WAVE_1_PANEL_RECOMMENDATION.md
```

And the final recommendation contains:

```text
20–24 total peptides
10–12 seed/scaffold families
≥8 candidates from high-confidence novel or novel classes
≤2 variants per family unless explicitly justified
2–4 controls
activity consensus from ≥3 predictors
safety/off-target annotation
hemolysis-risk annotation
novelty classification
synthesis/QC risk flag
clear reason for inclusion
clear reason for exclusion
```

---

## Target Score Impact

Current OpenAMP pre-wet-lab score:

```text
58 / 100
```

Expected after Wave 0.5 if implemented well:

```text
61–63 / 100 before wet lab
```

Reason:

```text
OpenAMP becomes not just a predicted-AMP panel,
but a diversified, novelty-aware, safety-aware candidate portfolio.
```

---

# Phase 1 — Freeze Current Evidence

## Objective

Lock the current panel and evidence state before adding new scaffolds.

## Tasks

Create:

```text
docs/WAVE_0_5_BASELINE.md
```

Include:

```text
current 20 candidates
seed family
rank
sequence
OpenAMP ensemble score
novelty class
CAMPR4 result
AMPScanner v2 result
Macrel result
AMPActiPred result
AntiCP result
HemoFinder result
current recommendation
```

## Required Output Columns

```csv
candidate_id,rank,seed,sequence,openamp_ensemble,novelty_class,campr4_vote,ampscanner_vote,macrel_amp_vote,ampactipred_abp_vote,anticp_class,hemofinder_risk,current_role
```

## Acceptance Criteria

The baseline file must clearly classify each current candidate as one of:

```text
LEAD
HIGH_UPSIDE_RISKY
CONTROL
SAR_CONTROL
DROP
PENDING
```

Recommended current roles:

| Seed     | Role                      |
| -------- | ------------------------- |
| SEED-006 | LEAD                      |
| SEED-008 | HIGH_UPSIDE_RISKY         |
| SEED-007 | PENDING / SAFETY_MIXED    |
| SEED-009 | PENDING / OFFTARGET_MIXED |
| SEED-001 | CONTROL                   |
| SEED-003 | SAR_CONTROL               |
| SEED-005 | LOW_PRIORITY              |

---

# Phase 2 — Define New Scaffold Search Space

## Objective

Add new independent scaffold families, not just more variants of existing families.

## New Scaffold Design Principles

Prioritize peptides that are:

```text
short to medium length: 10–25 AA
linear
cationic but not extreme
moderate hydrophobicity
moderate hydrophobic moment
low predicted hemolysis
low AntiCP/off-target risk
not Cys/disulfide-dependent if avoidable
simple synthesis profile
mechanistically different from current families
```

Avoid candidates that are:

```text
melittin-like
strongly venom/toxin-like
very hydrophobic
strongly hemolytic by predictors
many Cys / disulfide-dependent
long >35 AA
highly similar to known patented AMPs
obvious copies of famous AMPs
```

## Desired New Scaffold Categories

Search or generate from these broad categories:

```text
histatin-like / oral innate peptide fragments
low-hemolysis cationic helices
glycine-rich or low-hydrophobicity AMPs
short proline-rich intracellular-style peptides
dermaseptin-like but de-risked hydrophobicity
plant/insect AMP fragments without disulfide dependency
designed de novo low-hemolysis cationic peptides
low-aromatic alternatives to SEED-008
low-AntiCP alternatives to SEED-009
```

## Target Number

Generate/search:

```text
8–12 new seed families
5–20 raw variants per family
80–200 raw candidates total
```

Then filter down to:

```text
10–16 new candidates
5–8 new families
```

---

# Phase 3 — Candidate Generation / Discovery

## Objective

Produce a raw candidate pool from both database-inspired and de novo sources.

## Input Sources

Agents may use these sources:

```text
public AMP databases
published AMP families
existing OpenAMP feature space
de novo constrained sequence generation
low-hemolysis motif design
family-level mutation around weak-but-interesting scaffolds
```

## Generation Rules

Each new candidate must include:

```text
candidate_id
source_family
sequence
length
net_charge_pH74
hydrophobic_fraction
hydrophobic_moment
aromatic_fraction
boman_index
synthesis_risk_flags
initial_activity_score
initial_safety_score
novelty_proxy
generation_reason
```

## Candidate ID Format

Use:

```text
SEED-011_VAR_001
SEED-011_VAR_002
...
SEED-020_VAR_001
```

Do not reuse old seed IDs.

## Raw Candidate Output

Create:

```text
outputs/wave0_5_raw_candidates.csv
```

Required columns:

```csv
candidate_id,seed_family,sequence,length,source_type,generation_reason,net_charge_pH74,hydrophobic_fraction,hydrophobic_moment,aromatic_fraction,boman_index,initial_activity_score,initial_safety_score,novelty_proxy,synthesis_flags
```

## Acceptance Criteria

Raw pool must contain:

```text
≥80 candidates
≥8 new seed families
no invalid amino acid characters
no exact duplicates
no candidate shorter than 8 AA
no candidate longer than 35 AA unless justified
```

---

# Phase 4 — First-Pass Internal Filtering

## Objective

Reduce the raw pool to a manageable pre-external-predictor shortlist.

## Internal Gates

Candidate must pass:

```text
valid amino acid sequence
length 10–25 preferred
net charge positive
no extreme hydrophobicity
no severe synthesis flags
OpenAMP activity score above threshold
OpenAMP safety score above threshold
not exact duplicate of current panel
not near-duplicate of current controls
```

## Suggested Thresholds

Use current OpenAMP thresholds where available. If new thresholds are needed, commit them as source-code constants or a versioned config. Do not silently tune thresholds after seeing results.

Suggested starting rules:

```text
activity_score >= 0.70
safety_score >= 0.75
synthesis_score >= 0.75
novelty_proxy >= 0.50
max_similarity_to_current_panel < 0.80
```

For high-upside candidates, allow one controlled exception if documented:

```text
activity_score >= 0.80
safety_score >= 0.65
requires explicit HIGH_UPSIDE_RISKY label
```

## Output

Create:

```text
outputs/wave0_5_internal_shortlist.csv
```

Target size:

```text
30–60 candidates
8–12 seed families
```

## Acceptance Criteria

The shortlist must include:

```text
at least 8 new families
no family with more than 6 variants
all candidates pass basic sequence validity
all exclusions have reason codes
```

---

# Phase 5 — External Predictor Screen

## Objective

Run the same external predictor stack on the new shortlist.

## Activity Predictors

Use:

```text
CAMPR4 / CAMP-style predictor
AMPScanner v2
Macrel
AMPActiPred
OpenAMP internal activity score
```

Optional if available:

```text
dbAMP AMPpredictor
HMD-AMP
AMP0
```

## Safety / Off-Target Predictors

Use:

```text
HemoFinder
AntiCP2
Macrel hemolysis flag
OpenAMP safety score
```

## Important Interpretation Rule

Do not count AntiCP2 as AMP activity support.

AntiCP2 should be treated as:

```text
off-target / cytotoxicity / anticancer-like risk
```

HemoFinder should be treated as:

```text
hemolysis risk predictor
```

Macrel has two roles:

```text
Macrel AMP prediction -> activity signal
Macrel hemolysis prediction -> safety warning
```

## Output

Create:

```text
outputs/wave0_5_external_predict_results.csv
outputs/wave0_5_external_consensus.csv
outputs/wave0_5_safety_consensus.csv
docs/WAVE_0_5_EXTERNAL_PREDICTOR_SUMMARY.md
```

## Suggested External Consensus Columns

```csv
candidate_id,sequence,seed_family,campr4_vote,ampscanner_vote,macrel_amp_vote,ampactipred_abp_vote,activity_votes,total_activity_predictors,activity_consensus,anticp_class,hemofinder_risk,macrel_hemolysis_flag,safety_risk_level
```

## Activity Consensus Rule

```text
STRONG_ACTIVITY = ≥3 positive activity predictors
MODERATE_ACTIVITY = 2 positive activity predictors
WEAK_ACTIVITY = ≤1 positive activity predictor
```

## Safety Risk Rule

```text
LOW_RISK = HemoFinder low + AntiCP non-AntiCP + no Macrel hemolysis flag
MIXED_RISK = one safety warning
HIGH_RISK = two or more safety warnings
```

## Acceptance Criteria

At least:

```text
20 candidates with STRONG_ACTIVITY
10 candidates with STRONG_ACTIVITY + LOW/MIXED_RISK
6 candidates from new seed families with STRONG_ACTIVITY
```

If not achieved, go back to Phase 3 and generate more candidates.

---

# Phase 6 — Full Novelty / Prior-Art Screen

## Objective

Check whether candidates are truly novel or merely variants of known AMPs.

This is not activity prediction. This is lead qualification.

## Databases / Search Targets

Search against:

```text
APD3
DRAMP
DBAASP
UniProt
known public AMP candidate papers
Google Patents / Lens / WIPO where possible
current OpenAMP reference library
current OpenAMP candidate panel
```

## Similarity Rules

Classify every candidate as:

| Class                 | Rule                                 | Action                                |
| --------------------- | ------------------------------------ | ------------------------------------- |
| EXACT_MATCH           | 100% match                           | Exclude as lead                       |
| KNOWN_VARIANT         | ≥80% identity                        | Control/SAR only                      |
| CLOSE_RELATIVE        | 60–80% identity                      | Conditional                           |
| RELATED_NOVEL         | 40–60% identity                      | Keep with disclosure                  |
| HIGH_CONFIDENCE_NOVEL | <40% identity and no patent red flag | Lead candidate                        |
| PATENT_RISK           | patent/literature claim overlap      | Legal review before public disclosure |

## Output

Create:

```text
outputs/wave0_5_novelty_audit.csv
docs/WAVE_0_5_NOVELTY_AUDIT.md
```

Required columns:

```csv
candidate_id,sequence,best_database,best_hit_id,best_hit_sequence,best_identity,best_similarity,novelty_class,patent_risk,action
```

## Acceptance Criteria

Final candidate panel should contain:

```text
≥8 HIGH_CONFIDENCE_NOVEL or RELATED_NOVEL candidates
≤4 known/control/SAR candidates
0 exact matches as leads
0 unresolved patent-risk candidates as leads
```

---

# Phase 7 — Portfolio Selection

## Objective

Select a final Wave 1 panel that maximizes independent hit probability, not just per-peptide score.

## Final Panel Composition

Target:

```text
20–24 peptides
10–12 independent families
1–2 candidates per lead family
2–4 controls
```

Suggested composition:

```text
8–10 balanced novel candidates
4–6 high-upside / higher-risk candidates
3–4 controls / SAR anchors
2–4 reserve candidates
```

## Selection Score

Create a portfolio score that rewards diversity.

Suggested formula:

```text
portfolio_priority =
  0.25 * activity_consensus_score
+ 0.20 * safety_score
+ 0.20 * novelty_score
+ 0.15 * family_diversity_bonus
+ 0.10 * synthesis_feasibility
+ 0.10 * mechanism_diversity
```

Penalties:

```text
- high hemolysis risk
- AntiCP-positive off-target risk
- patent-risk flag
- close-relative novelty
- family overrepresentation
- severe synthesis flag
```

## Hard Portfolio Rules

```text
No more than 2 lead candidates from the same family.
At least 8 families must be represented.
At least 1 positive control must be included.
At least 1 lower-risk negative/safety comparator is useful if scientifically justified.
Known variants cannot be labeled as breakthrough leads.
High-risk/high-upside candidates must be explicitly labeled.
```

## Output

Create:

```text
docs/WAVE_1_PANEL_RECOMMENDATION.md
outputs/wave1_final_panel.csv
outputs/wave1_reserve_panel.csv
```

## Final Panel CSV Columns

```csv
candidate_id,sequence,seed_family,panel_role,activity_consensus,safety_risk,novelty_class,synthesis_flags,reason_for_inclusion,reason_for_exclusion_if_any
```

Panel roles:

```text
BALANCED_LEAD
HIGH_UPSIDE_RISKY
POSITIVE_CONTROL
SAR_CONTROL
RESERVE
DROP
```

---

# Phase 8 — Update Evidence Certificates

## Objective

Every final candidate must have a machine-readable evidence certificate.

## Certificate Fields

For each final candidate, create/update:

```text
outputs/evidence_wave0_5/{candidate_id}.json
```

Required fields:

```json
{
  "candidate_id": "",
  "sequence": "",
  "seed_family": "",
  "panel_role": "",
  "openamp_scores": {},
  "external_activity_predictors": {},
  "safety_predictors": {},
  "novelty_audit": {},
  "synthesis_qc": {},
  "known_risks": [],
  "reason_for_inclusion": "",
  "reason_for_exclusion": "",
  "wet_lab_claim_status": "NO_WET_LAB_EVIDENCE"
}
```

## Acceptance Criteria

Every final panel candidate must have:

```text
activity evidence
safety evidence
novelty evidence
synthesis risk evidence
role label
no biological claim
```

---

# Phase 9 — Update Docs

## Required New Docs

Create:

```text
docs/WAVE_0_5_SCAFFOLD_DIVERSIFICATION_PLAN.md
docs/WAVE_0_5_BASELINE.md
docs/WAVE_0_5_EXTERNAL_PREDICTOR_SUMMARY.md
docs/WAVE_0_5_NOVELTY_AUDIT.md
docs/WAVE_1_PANEL_RECOMMENDATION.md
```

Update:

```text
docs/METRICS_CURRENT.md
docs/EXTERNAL_PREDICTOR_CONSENSUS.md
docs/NOVELTY_AUDIT_FULL.md
docs/DECISION_RULES.md
docs/IP_PLAN.md
docs/EXPERT_REVIEW_PACK.md
docs/DISCOVERY_PREDICTION.md
docs/ROADMAP.md
```

## Required Language

Every public doc must include:

```text
No wet-lab evidence yet.
All activity and safety values are computational predictions.
Wet-lab validation by qualified collaborators is required.
Known/control candidates are not novelty claims.
High-risk candidates are labeled explicitly.
```

---

# Phase 10 — Decision Gates

## Add Wave 0.5 Gates

Create or extend:

```text
src/openamp_foundry/gates/wave0_5_gate_checker.py
```

## Proposed Gates

### Gate W0.5-1 — Family Diversity

```text
PASS if final panel contains ≥8 independent seed families.
```

### Gate W0.5-2 — Family Redundancy

```text
PASS if no lead family contributes more than 2 lead candidates.
```

### Gate W0.5-3 — Activity Consensus

```text
PASS if ≥70% of lead candidates have STRONG_ACTIVITY.
```

### Gate W0.5-4 — Safety Annotation

```text
PASS if 100% of candidates have HemoFinder, AntiCP, and Macrel hemolysis annotations.
```

### Gate W0.5-5 — Novelty Qualification

```text
PASS if ≥8 candidates are HIGH_CONFIDENCE_NOVEL or RELATED_NOVEL.
```

### Gate W0.5-6 — Control Integrity

```text
PASS if known/control candidates are labeled as CONTROL or SAR_CONTROL, not LEAD.
```

### Gate W0.5-7 — Claim Safety

```text
PASS if docs contain no unsupported wet-lab, drug, antibiotic, cure, or clinical claims.
```

## Acceptance Criteria

Running:

```bash
make wave0-5-gate-check
```

must produce:

```text
PASS / FAIL / PENDING
```

for every gate.

---

# Suggested PR Plan

## PR 1 — Baseline Freeze

Branch:

```text
wave0-5-baseline
```

Files:

```text
docs/WAVE_0_5_BASELINE.md
outputs/wave0_5_baseline.csv
```

Acceptance:

```text
Current 20 candidates classified into LEAD / CONTROL / RISK / DROP roles.
```

---

## PR 2 — Raw Candidate Generation

Branch:

```text
wave0-5-generate-candidates
```

Files:

```text
scripts/generate_wave0_5_candidates.py
outputs/wave0_5_raw_candidates.csv
```

Acceptance:

```text
≥80 raw candidates
≥8 new seed families
no invalid sequences
```

---

## PR 3 — Internal Filter

Branch:

```text
wave0-5-internal-filter
```

Files:

```text
scripts/filter_wave0_5_candidates.py
outputs/wave0_5_internal_shortlist.csv
```

Acceptance:

```text
30–60 shortlisted candidates
all exclusion reasons recorded
```

---

## PR 4 — External Predictor Integration

Branch:

```text
wave0-5-external-consensus
```

Files:

```text
outputs/wave0_5_external_predict_results.csv
outputs/wave0_5_external_consensus.csv
outputs/wave0_5_safety_consensus.csv
docs/WAVE_0_5_EXTERNAL_PREDICTOR_SUMMARY.md
```

Acceptance:

```text
activity consensus and safety consensus available for every shortlisted candidate.
```

---

## PR 5 — Novelty / Prior-Art Audit

Branch:

```text
wave0-5-novelty-audit
```

Files:

```text
scripts/run_wave0_5_novelty_audit.py
outputs/wave0_5_novelty_audit.csv
docs/WAVE_0_5_NOVELTY_AUDIT.md
```

Acceptance:

```text
all final candidates have novelty class and action.
```

---

## PR 6 — Final Panel Selection

Branch:

```text
wave1-panel-selection
```

Files:

```text
scripts/select_wave1_panel.py
outputs/wave1_final_panel.csv
outputs/wave1_reserve_panel.csv
docs/WAVE_1_PANEL_RECOMMENDATION.md
```

Acceptance:

```text
20–24 final candidates
10–12 families
2–4 controls
no unlabeled high-risk candidates
```

---

## PR 7 — Evidence Certificates + Gates

Branch:

```text
wave0-5-evidence-gates
```

Files:

```text
outputs/evidence_wave0_5/*.json
src/openamp_foundry/gates/wave0_5_gate_checker.py
tests/test_wave0_5_gates.py
docs/DECISION_RULES.md
```

Acceptance:

```text
all final candidates have evidence certificates
all Wave 0.5 gates implemented
tests pass
```

---

# Agent Operating Rules

Each agent must follow these rules:

```text
1. Do not change thresholds silently.
2. Do not relabel known variants as novel.
3. Do not optimize toward hemolysis, cytotoxicity, or mammalian-cell killing.
4. Do not add wet-lab protocols.
5. Do not make biological efficacy claims.
6. Every exclusion must have a reason.
7. Every candidate must be traceable from generation → filtering → external predictors → novelty audit → final role.
8. Every PR must update docs and tests.
9. Every PR must keep current metrics reproducible.
10. If a result is uncertain, mark it UNCERTAIN, not PASS.
```

---

# Final Deliverable

Wave 0.5 is complete when the repo can answer:

```text
Which candidates should be synthesized first?
Why these candidates?
Which families are independent?
Which candidates are controls?
Which candidates are high-risk/high-upside?
Which candidates are low-risk balanced leads?
Which candidates were excluded and why?
Which evidence supports each decision?
What still requires wet-lab validation?
```

The final expected answer should look like:

```text
OpenAMP Wave 1 recommends 20–24 peptides across 10–12 independent scaffold families.

The panel includes:
- balanced novel leads,
- high-upside risky probes,
- positive/SAR controls,
- reserve candidates.

All candidates have:
- internal OpenAMP scores,
- external AMP predictor consensus,
- safety/off-target screen,
- hemolysis-risk screen,
- novelty/prior-art classification,
- synthesis/QC flags,
- machine-readable evidence certificates.

No antimicrobial activity is claimed until qualified wet-lab validation.
```

---

# North Star

OpenAMP should not try to be the biggest AMP generator.

It should become:

```text
the most rigorous, auditable, safety-aware, novelty-aware AMP candidate evidence foundry
```

Wave 0.5 moves OpenAMP toward that standard.

