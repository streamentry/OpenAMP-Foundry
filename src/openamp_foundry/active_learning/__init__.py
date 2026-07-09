"""Active learning: second-batch candidate selection for assay panels.

After an initial batch is tested in the lab and the recalibration pipeline
computes weight updates, the active-learning selector picks the next batch
of candidates. It balances:

- **Uncertainty**: candidates where the model is most unsure (high
  disagreement, or ensemble score near 0.5).
- **Diversity**: candidates that are structurally distinct from the first
  batch, to explore new sequence space.
- **Safety**: candidates that pass a minimum safety/toxicity threshold.

The benchmark module validates whether the selector can recover known active
candidates faster than random baseline — a code-path integrity check.

The strategy-comparison report runs multiple selection strategies (exploitation,
exploration, diversity, combined, random) on the same synthetic pool and ranks
them by recovery recall, preventing one-selector bias.
"""

from openamp_foundry.active_learning.benchmark import (
    ActiveLearningBenchmarkResult,
    RecoveryRound,
    generate_benchmark_pool,
    run_active_learning_benchmark,
    write_benchmark_pool,
)
from openamp_foundry.active_learning.selector import (
    BatchSelection,
    select_batch_2,
)
from openamp_foundry.active_learning.strategy_comparison import (
    STRATEGY_WEIGHTS,
    StrategyComparisonReport,
    StrategyResult,
    run_strategy_comparison,
    write_comparison_json,
    write_comparison_markdown,
)

__all__ = [
    "ActiveLearningBenchmarkResult",
    "BatchSelection",
    "RecoveryRound",
    "STRATEGY_WEIGHTS",
    "StrategyComparisonReport",
    "StrategyResult",
    "generate_benchmark_pool",
    "run_active_learning_benchmark",
    "run_strategy_comparison",
    "select_batch_2",
    "write_benchmark_pool",
    "write_comparison_json",
    "write_comparison_markdown",
]
