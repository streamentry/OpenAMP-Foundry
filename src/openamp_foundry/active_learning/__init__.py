"""Active learning: second-batch candidate selection for assay panels.

After an initial batch is tested in the lab and the recalibration pipeline
computes weight updates, the active-learning selector picks the next batch
of candidates. It balances:

- **Uncertainty**: candidates where the model is most unsure (high
  disagreement, or ensemble score near 0.5).
- **Diversity**: candidates that are structurally distinct from the first
  batch, to explore new sequence space.
- **Safety**: candidates that pass a minimum safety/toxicity threshold.
"""

from openamp_foundry.active_learning.selector import (
    BatchSelection,
    select_batch_2,
)

__all__ = [
    "BatchSelection",
    "select_batch_2",
]
