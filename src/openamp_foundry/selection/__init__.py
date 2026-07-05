"""Selection layer for OpenAMP Foundry.

Diversity-aware selection of pilot panels from a ranked candidate pool.
Provides greedy diverse selection, Pareto ranking, and the pilot-panel
selector used by `openamp-foundry pilot-panel`.
"""

from openamp_foundry.selection.diversity import greedy_diverse_select
from openamp_foundry.selection.pareto import rank_candidates, select_top
from openamp_foundry.selection.pilot import select_pilot_panel
from openamp_foundry.selection.structural_class import classify_structural_class

__all__ = [
    "classify_structural_class",
    "greedy_diverse_select",
    "rank_candidates",
    "select_pilot_panel",
    "select_top",
]
