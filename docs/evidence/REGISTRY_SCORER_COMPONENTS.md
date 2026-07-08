# Scorer Component Registry

Registry of all scoring components in the pipeline.

| Scorer | Module | Purpose | Weight |
|--------|--------|---------|:------:|
| activity | scoring/activity.py | Antimicrobial activity-likeness | 0.40 |
| safety | scoring/safety.py | Hemolysis/toxicity risk | 0.25 |
| synthesis | scoring/synthesis.py | Synthesis feasibility | 0.15 |
| novelty | scoring/novelty.py | Novelty vs known references | 0.20 |
| ensemble | scoring/ensemble.py | Weighted combination | — |
| boman | scoring/boman.py | Boman index (binding potential) | — |
| serum_stability | scoring/stability.py | Protease resistance | — |
| hemolysis_risk | scoring/hemolysis.py | Dedicated hemolysis risk | — |
| rich_selectivity | scoring/selectivity_rich.py | Evidence-based selectivity | — |
| expert | scoring/expert.py | Safety-aware composite | — |

## Rules
- New scorers should be registered here.
- The registry should be updated when weights change.
- Each scorer should have a module in `src/openamp_foundry/scoring/`.
